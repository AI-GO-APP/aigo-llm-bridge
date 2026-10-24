"""Concurrent metadata reads never pool an inference CLI or cache an auth verdict."""
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time

import pytest
import json
from types import SimpleNamespace

from desktop_bridge import providers
from desktop_bridge.errors import BridgeError
from desktop_bridge.execution_budget import Budget, scope
from desktop_bridge.process import Child

SETTINGS={'timeout_s':3}


@pytest.mark.parametrize('mode', ['negative_then_ready','generation_then_stable','always_negative','always_changing'])
def test_cold_claude_revalidates_metadata_once_and_starts_at_most_one_inference(monkeypatch,tmp_path,mode):
    generation=[0];queries=[];children=[]
    monkeypatch.setattr(providers,'auth_generation',lambda *_:str(generation[0]))
    def status(*args,**kwargs):
        queries.append(True)
        if mode=='always_changing' or (mode=='generation_then_stable' and len(queries)==1):generation[0]+=1
        return {'ready':mode!='always_negative' and not (mode=='negative_then_ready' and len(queries)==1)}
    monkeypatch.setattr(providers,'status',status)
    monkeypatch.setattr(providers,'executable',lambda *_:'synthetic-cli')
    class FakeChild:
        proc=SimpleNamespace(returncode=0)
        def __init__(self,*args):children.append(True)
        def communicate(self,*args):return json.dumps({'type':'result','result':'PONG','usage':{'input_tokens':3,'output_tokens':2},'modelUsage':{'fixture':{}}}).encode()
        def close(self):pass
    monkeypatch.setattr(providers,'Child',FakeChild)
    class Settings(dict):pass
    settings=Settings(timeout_s=3);settings.status_reads=providers.StatusReads()
    spec=SimpleNamespace(model={'native':'fixture'},system='',schema=None,effort=None,messages=[{'parts':[{'type':'text','text':'Synthetic'}]}])
    succeeds=mode in {'negative_then_ready','generation_then_stable'}
    if succeeds:assert providers.call_claude(spec,settings,threading.Event(),tmp_path)[0]=='PONG'
    else:
        with pytest.raises(BridgeError) as error:providers.call_claude(spec,settings,threading.Event(),tmp_path)
        assert error.value.category=='provider_authentication'
    assert len(queries)==2 and len(children)==int(succeeds)
    assert sum(settings.status_reads.snapshot().values())==1


def test_cold_claude_cancel_before_recheck_and_codex_never_rechecks(monkeypatch,tmp_path):
    monkeypatch.setattr(providers,'auth_generation',lambda *_:'same')
    for provider in ('claude','codex'):
        cancel=threading.Event();calls=[]
        def status(*args,**kwargs):calls.append(True);cancel.set();return {'ready':False}
        monkeypatch.setattr(providers,'status',status)
        if provider=='claude':
            with pytest.raises(BridgeError) as error:providers.inference_status(provider,SETTINGS,cancel,tmp_path)
            assert error.value.category=='cancelled'
        else:assert not providers.inference_status(provider,SETTINGS,cancel,tmp_path)['ready']
        assert len(calls)==1


def test_64_overlapping_reads_share_one_check_and_next_read_is_fresh(monkeypatch,tmp_path):
    calls=[];arrivals=[];ready=threading.Event();release=threading.Event()
    def generation(*_):
        arrivals.append(1)
        if len(arrivals)>=64:ready.set()
        return 'same'
    def status(*_,**kwargs):
        calls.append(1);assert release.wait(3);return {'ready':True}
    monkeypatch.setattr(providers,'auth_generation',generation)
    monkeypatch.setattr(providers,'status',status)
    reads=providers.StatusReads()
    def read(_):
        with scope(Budget(time.monotonic()+3,threading.Event())):
            return reads.read('claude',SETTINGS,threading.Event(),tmp_path)
    with ThreadPoolExecutor(max_workers=64) as clients:
        futures=[clients.submit(read,i) for i in range(64)]
        assert ready.wait(2);time.sleep(.05);assert calls==[1]
        release.set();assert all(f.result()=={'ready':True} for f in futures)
    assert reads.inflight=={}
    assert read(0)=={'ready':True} and len(calls)==2


@pytest.mark.parametrize('cause,status_code',[('deadline',408),('cancel',499)])
def test_waiter_uses_own_deadline_and_cancellation(monkeypatch,tmp_path,cause,status_code):
    started=threading.Event();release=threading.Event()
    monkeypatch.setattr(providers,'auth_generation',lambda *_:'same')
    def status(*_,**kwargs):
        started.set();assert release.wait(3);return {'ready':True}
    monkeypatch.setattr(providers,'status',status)
    reads=providers.StatusReads()
    with ThreadPoolExecutor(max_workers=1) as clients:
        leader=clients.submit(reads.read,'claude',SETTINGS,threading.Event(),tmp_path)
        assert started.wait(1)
        cancel=threading.Event()
        if cause=='cancel':threading.Timer(.1,cancel.set).start()
        began=time.monotonic()
        try:
            with scope(Budget(time.monotonic()+(.12 if cause=='deadline' else 2),cancel)),pytest.raises(BridgeError) as error:
                reads.read('claude',SETTINGS,cancel,tmp_path)
            assert error.value.status==status_code and time.monotonic()-began<.5
        finally:release.set()
        assert leader.result()=={'ready':True} and not reads.inflight


def test_cancelled_leader_does_not_cancel_other_callers(monkeypatch,tmp_path):
    started=threading.Event();cancel=threading.Event();calls=[]
    monkeypatch.setattr(providers,'auth_generation',lambda *_:'same')
    def status(*_,**kwargs):
        calls.append(1)
        if len(calls)==1:
            started.set();assert cancel.wait(2);raise BridgeError(499,'cancelled','synthetic')
        return {'ready':True}
    monkeypatch.setattr(providers,'status',status)
    reads=providers.StatusReads()
    with ThreadPoolExecutor(max_workers=2) as clients:
        leader=clients.submit(reads.read,'claude',SETTINGS,cancel,tmp_path)
        assert started.wait(1)
        waiter=clients.submit(reads.read,'claude',SETTINGS,threading.Event(),tmp_path)
        time.sleep(.05);cancel.set()
        with pytest.raises(BridgeError):leader.result()
        assert waiter.result()=={'ready':True} and len(calls)==2 and not reads.inflight


def test_generation_change_refuses_old_verdict(monkeypatch,tmp_path):
    generation=['old'];started=threading.Event();release=threading.Event()
    monkeypatch.setattr(providers,'auth_generation',lambda *_:generation[0])
    def status(*_,**kwargs):
        started.set();assert release.wait(2);return {'ready':True}
    monkeypatch.setattr(providers,'status',status)
    reads=providers.StatusReads()
    with ThreadPoolExecutor(max_workers=1) as clients:
        future=clients.submit(reads.read,'claude',SETTINGS,threading.Event(),tmp_path)
        assert started.wait(1);generation[0]='new';release.set()
        with pytest.raises(BridgeError) as error:future.result()
        assert error.value.status==503 and not reads.inflight


def test_cancellable_auth_child_is_reaped_before_error(monkeypatch,tmp_path):
    children=[]
    def child(*args,**kwargs):
        value=Child([sys.executable,'-c','import time;time.sleep(30)'],tmp_path,providers.environment())
        children.append(value);return value
    monkeypatch.setattr(providers,'Child',child)
    monkeypatch.setattr(providers,'executable',lambda *_:sys.executable)
    cancel=threading.Event();threading.Timer(.12,cancel.set).start()
    began=time.monotonic()
    with pytest.raises(BridgeError) as error:providers.status('claude',{},cancel=cancel,cwd=tmp_path)
    assert error.value.status==499 and time.monotonic()-began<1
    assert children[0].proc.poll() is not None


def test_codex_auth_can_read_stderr_without_retaining_it(monkeypatch,tmp_path):
    def child(*args,**kwargs):
        return Child([sys.executable,'-c',"import sys;sys.stderr.write('Logged in using ChatGPT')"],tmp_path,providers.environment())
    monkeypatch.setattr(providers,'Child',child)
    monkeypatch.setattr(providers,'executable',lambda *_:sys.executable)
    assert providers.status('codex',{},cancel=threading.Event(),cwd=tmp_path)=={'provider':'codex','ready':True,'method':'ChatGPT'}


def test_launch_pacer_spaces_starts_without_reserving_cancelled_future_slots():
    pacer=providers.LaunchPacer(interval=.01)
    def enter(_):
        # Spacing is the assertion here, not the hosted runner's scheduling SLO.
        # The independent short-budget case below still requires expiry.
        pacer.wait(threading.Event());return time.monotonic()
    with ThreadPoolExecutor(max_workers=64) as clients:starts=sorted(clients.map(enter,range(64)))
    assert starts[-1]-starts[0]>=.6
    pacer.next_start=time.monotonic()+.2
    until=pacer.next_start
    with scope(Budget(time.monotonic()+.04,threading.Event())),pytest.raises(BridgeError) as error:
        pacer.wait(threading.Event())
    assert error.value.status==408 and pacer.next_start==until


def test_auth_generation_is_rechecked_after_waiting_to_launch(monkeypatch,tmp_path):
    generation=['old']
    monkeypatch.setattr(providers,'auth_generation',lambda *_:generation[0])
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    class Pacer:
        def wait(self,_):generation[0]='new'
    class Settings:
        launch_pacer=Pacer()
        def get(self,name):return 3
    with pytest.raises(BridgeError) as error:
        providers.inference_status('claude',Settings(),threading.Event(),tmp_path,pace=True)
    assert error.value.status==503


def test_simple_requests_do_not_wait_for_fixed_structure_startup(monkeypatch,tmp_path):
    calls=[]
    monkeypatch.setattr(providers,'auth_generation',lambda *_:'same')
    monkeypatch.setattr(providers,'status',lambda *_,**kwargs:{'ready':True})
    class Pacer:
        def wait(self,_):calls.append(1)
    class Settings:
        launch_pacer=Pacer()
        def get(self,name):return 3
    assert providers.inference_status('claude',Settings(),threading.Event(),tmp_path)['ready']
    assert not calls
    assert providers.inference_status('claude',Settings(),threading.Event(),tmp_path,pace=True)['ready']
    assert calls==[1]
