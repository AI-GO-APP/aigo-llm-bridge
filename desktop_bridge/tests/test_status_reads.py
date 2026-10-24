"""Concurrent metadata reads never pool an inference CLI or cache an auth verdict."""
from concurrent.futures import ThreadPoolExecutor
import sys
import threading
import time

import pytest

from desktop_bridge import providers
from desktop_bridge.errors import BridgeError
from desktop_bridge.execution_budget import Budget, scope
from desktop_bridge.process import Child

SETTINGS={'timeout_s':3}


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
