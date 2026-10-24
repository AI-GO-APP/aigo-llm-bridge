"""Synthetic executable, no provider/network: lifecycle and per-process isolation."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
import threading
import time

import pytest

from desktop_bridge import providers
from desktop_bridge.codex_session import CodexSession
from desktop_bridge.contract import Inference
from desktop_bridge.errors import BridgeError
from tools.warm_cli_pool import SingleUsePool


SCRIPT = r'''
import json, os, sys, time
model = None
for line in sys.stdin:
    m = json.loads(line); method = m['method']; p = m['params']
    result = {}
    if method == 'thread/start':
        model = p['model']
        result = {'model':model,'thread':{'id':str(os.getpid()),'ephemeral':True,'path':None}}
    elif method == 'turn/start':
        text = p['input'][0]['text']
        schema = p.get('outputSchema',{}).get('properties',{})
        if 'noul' in schema: text = json.dumps({'noul':.75})
        if 'probabilities' in schema:
            n = schema['probabilities']['minItems']
            text = json.dumps({'probabilities':[1.0/n]*n})
        if text == '__CRASH__': sys.exit(1)
        if text == '__WAIT__': time.sleep(30)
        def emit(method, params):
            print(json.dumps({'method':method,'params':params}),flush=True)
        emit('item/agentMessage/delta',{'threadId':str(os.getpid()),'delta':text})
        emit('thread/tokenUsage/updated',{'threadId':str(os.getpid()),
             'tokenUsage':{'total':{'inputTokens':len(text),'outputTokens':1}}})
        emit('turn/completed',{'threadId':str(os.getpid()),'turn':{'status':'completed'}})
    if 'id' in m: print(json.dumps({'id':m['id'],'result':result}),flush=True)
'''


class FakeResource:
    def __init__(self, cancel, deadline):
        self.directory = tempfile.TemporaryDirectory(prefix='warm-synthetic-')
        self.cwd = self.directory.name
        try:
            self.session = CodexSession([sys.executable, '-u', '-c', SCRIPT], self.cwd, None,
                                        cancel, deadline - time.monotonic())
        except BaseException:
            self.directory.cleanup()
            raise

    def healthy(self):
        return self.session.healthy()

    def close(self):
        self.session.close()
        self.directory.cleanup()


def wait_for(predicate, timeout=5):
    until = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < until
        time.sleep(.01)


@contextmanager
def pool_fixture(**kwargs):
    resources = []
    def factory(cancel, deadline):
        r = FakeResource(cancel, deadline)
        resources.append(r)
        return r
    pool = SingleUsePool(factory, lambda: 'generation', **kwargs)
    try:
        yield pool, resources
    finally:
        pool.close()
        assert not pool.entries
        assert all(r.session.child.proc.poll() is not None and not Path(r.cwd).exists() for r in resources)


def spec_for(text, model='synthetic-model-a', system='synthetic system'):
    return Inference({'provider':'codex','native':model,'id':'synthetic'},
        [{'role':'user','parts':[{'type':'text','text':text}]}], system, None, 'text', None)


def test_100_pairs_cross_key_model_system_never_share_process_or_usage(monkeypatch):
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    with pool_fixture(target=3, limit=8) as (pool, resources):
        processes = set(); lock = threading.Lock()
        def call(index):
            # Each pair represents independent key/model/system routing. This is
            # transport isolation evidence, not HTTP key authorization acceptance.
            marker = f'key-{index % 2}-pair-{index // 2}'
            spec = spec_for(marker, 'synthetic-model-' + str(index % 2), 'system-' + marker)
            with pool.lease(threading.Event(), time.monotonic()+10) as resource:
                with lock:
                    assert resource.session.child.proc.pid not in processes
                    processes.add(resource.session.child.proc.pid)
                result = providers.call_codex(spec, {'timeout_s':5}, threading.Event(), resource.cwd,
                                              session=resource.session)
                assert result[0] == marker and result[3] == spec.model['native']
                assert result[1]['prompt_tokens'] == len(marker)
                assert resource.session.sent['turn/start'] == 1
                with pytest.raises(BridgeError):
                    resource.session.claim(resource.cwd)
        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(call, range(200)))
        assert len(processes) == 200
        assert pool.snapshot()['peak'] <= 8
        assert all(r.session.sent['turn/start'] <= 1 for r in resources)


def test_cancel_one_lease_does_not_cancel_another_and_never_replays(monkeypatch):
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    with pool_fixture(target=2, limit=2) as (pool, resources):
        wait_for(lambda: pool.snapshot()['idle'] == 2)
        cancel = threading.Event()
        def blocked():
            with pool.lease(cancel, time.monotonic()+5) as resource:
                with pytest.raises(BridgeError) as error:
                    providers.call_codex(spec_for('__WAIT__'), {'timeout_s':5}, cancel,
                                         resource.cwd, session=resource.session)
                assert error.value.category == 'cancelled'
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(blocked)
            wait_for(lambda: any(r.session.sent['turn/start'] for r in resources))
            cancel.set()
            with pool.lease(threading.Event(), time.monotonic()+5) as resource:
                assert providers.call_codex(spec_for('other-key'), {'timeout_s':5}, threading.Event(),
                                             resource.cwd, session=resource.session)[0] == 'other-key'
            future.result(timeout=5)
        assert sum(r.session.sent['turn/start'] for r in resources) == 2


@pytest.mark.parametrize('text,category', [('__CRASH__','provider_error'), ('__WAIT__','timeout')])
def test_post_start_failure_has_no_automatic_retry(monkeypatch,text,category):
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    with pool_fixture(target=0, limit=1) as (pool, resources):
        with pytest.raises(BridgeError) as error:
            with pool.lease(threading.Event(), time.monotonic()+5) as resource:
                providers.call_codex(spec_for(text), {'timeout_s':.1}, threading.Event(),
                                     resource.cwd, session=resource.session)
        assert error.value.category == category
        assert len(resources) == 1 and resources[0].session.sent['turn/start'] == 1
        assert pool.snapshot()['total'] == 0


def test_idle_zero_work_ttl_generation_pause_and_zero_resident():
    generation = ['a']; resources = []
    def factory(cancel,deadline):
        r = FakeResource(cancel,deadline); resources.append(r); return r
    pool = SingleUsePool(factory, lambda:generation[0], target=1, limit=2, ttl=.2)
    try:
        wait_for(lambda:pool.snapshot()['idle']==1)
        first = resources[0]
        generation[0] = 'b'
        wait_for(lambda:first.session.closed)
        wait_for(lambda:pool.snapshot()['idle']==1)
        second = resources[-1]
        wait_for(lambda:second.session.closed)
        pool.pause()
        wait_for(lambda:pool.snapshot()['total']==0)
        before = len(resources)
        pool.configure(0,1); pool.resume(); time.sleep(.25)
        assert len(resources) == before
        assert all(r.session.sent['thread/start']==r.session.sent['turn/start']==0 for r in resources)
        assert all(r.session.idle_work_events == 0 for r in resources)
    finally:
        pool.close()


@pytest.mark.parametrize('target,limit', [(2,1),(-1,1),(1,65),(True,2),(1,False)])
def test_capacity_contract_rejects_resident_above_concurrency(target,limit):
    with pytest.raises(ValueError):
        SingleUsePool(None,None,target=target,limit=limit)


def test_saturated_pool_wait_is_cancellable_and_refill_cannot_exceed_limit():
    with pool_fixture(target=1, limit=1) as (pool, _):
        cancel = threading.Event()
        with pool.lease(threading.Event(), time.monotonic()+5):
            cancel.set()
            with pytest.raises(BridgeError):
                with pool.lease(cancel, time.monotonic()+1):
                    pytest.fail('must not create another process')
            assert pool.snapshot()['total'] == 1
        assert pool.snapshot()['peak'] == 1


def test_refill_failure_backoff_and_stop_during_startup():
    attempts = []
    def fail(cancel,deadline):
        attempts.append(time.monotonic())
        raise OSError('synthetic')
    pool = SingleUsePool(fail,lambda:'a',target=1,limit=1,backoff=.02)
    time.sleep(.18)
    pool.close()
    assert 2 <= len(attempts) <= 5
    assert not pool.entries
    def blocked(cancel,deadline):
        cancel.wait(2)
        raise BridgeError(499,'cancelled','synthetic')
    pool = SingleUsePool(blocked,lambda:'a',target=1,limit=1)
    wait_for(lambda:pool.snapshot()['starting']==1)
    began=time.monotonic();pool.close()
    assert time.monotonic()-began < 1 and not pool.entries


def test_generation_change_during_auth_check_rejects_before_thread(monkeypatch):
    with pool_fixture(target=0, limit=1) as (pool, _):
        with pool.lease(threading.Event(), time.monotonic()+5) as resource:
            resource.session.generation = 'old'
            monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
            monkeypatch.setattr(providers, 'auth_generation', lambda *_:'new')
            with pytest.raises(BridgeError) as error:
                providers.call_codex(spec_for('synthetic'), {'timeout_s':5}, threading.Event(),
                                     resource.cwd, session=resource.session)
            assert error.value.category == 'provider_authentication'
            assert resource.session.sent['thread/start'] == resource.session.sent['turn/start'] == 0


def test_foreign_thread_event_is_rejected_and_not_replayed(monkeypatch):
    with tempfile.TemporaryDirectory() as cwd:
        session = CodexSession([sys.executable,'-u','-c',SCRIPT.replace(
            "'threadId':str(os.getpid())", "'threadId':'foreign-thread'" )],cwd,None,threading.Event(),3)
        monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
        with pytest.raises(BridgeError) as error:
            providers.call_codex(spec_for('synthetic'), {'timeout_s':3}, threading.Event(),cwd,session=session)
        assert error.value.category == 'session_isolation'
        assert session.sent['turn/start'] == 1 and session.closed


@pytest.mark.parametrize('payload', ["'x'*1000", "('x'*100+'\\n')*1000"])
def test_bounded_line_and_queue_overflow_cleanup(monkeypatch,tmp_path,payload):
    import desktop_bridge.codex_session as module
    from desktop_bridge.process import Child
    children = []
    def child(*args):
        value = Child(*args);children.append(value);return value
    monkeypatch.setattr(module,'Child',child)
    monkeypatch.setattr(CodexSession,'MAX_LINE',256)
    monkeypatch.setattr(CodexSession,'MAX_BUFFER',512)
    script = 'import sys; sys.stdout.write('+payload+'); sys.stdout.flush(); import time; time.sleep(10)'
    with pytest.raises(BridgeError) as error:
        CodexSession([sys.executable,'-u','-c',script],tmp_path,None,threading.Event(),2)
    assert error.value.category == 'output_too_large'
    assert children[0].proc.poll() is not None


def test_init_failure_and_reader_start_failure_release_owned_process(monkeypatch,tmp_path):
    import desktop_bridge.codex_session as module
    from desktop_bridge.process import Child
    children=[]
    def child(*args):
        value=Child(*args);children.append(value);return value
    monkeypatch.setattr(module,'Child',child)
    with pytest.raises(BridgeError):
        CodexSession([sys.executable,'-c','pass'],tmp_path,None,threading.Event(),1)
    assert children[-1].proc.poll() is not None
    def fail(_):raise RuntimeError('synthetic thread start failure')
    monkeypatch.setattr(module.threading.Thread,'start',fail)
    with pytest.raises(RuntimeError):
        CodexSession([sys.executable,'-c','import time;time.sleep(10)'],tmp_path,None,threading.Event(),1)
    assert children[-1].proc.poll() is not None


def test_cli_update_during_refill_discards_stale_process_before_leasing():
    generation=['a'];created=[]
    def factory(cancel,deadline):
        resource=FakeResource(cancel,deadline);created.append(resource)
        if len(created)==1:generation[0]='b'
        return resource
    pool=SingleUsePool(factory,lambda:generation[0],target=1,limit=1)
    try:
        wait_for(lambda:pool.snapshot()['idle']==1)
        assert created[0].session.closed
        with pool.lease(threading.Event(),time.monotonic()+5) as resource:
            assert resource is not created[0]
            with pytest.raises(ValueError):pool.configure(0,1)
    finally:pool.close()


@pytest.mark.parametrize('crash_second',[False,True])
def test_multiquestion_runtime_receipts_preserve_known_usage_across_fresh_leases(tmp_path,monkeypatch,crash_second):
    import uuid
    from desktop_bridge.service import Runtime
    from desktop_bridge.store import Store
    monkeypatch.setattr(providers, 'inference_status', lambda *_: {'ready':True})
    if crash_second:
        monkeypatch.setattr(sys.modules[__name__], 'SCRIPT', SCRIPT.replace(
            "if 'probabilities' in schema:", "if 'probabilities' in schema: sys.exit(1)\n        if 'probabilities' in schema:"))
    store=Store(tmp_path);_,key=store.create_key('synthetic',['codex']);caller=store.authenticate(key)
    body={'model':'openai/gpt-6.1-sol','state':'synthetic blue object','questions':{
        'a':{'type':'noul','instructions':'blue?'},
        'b':{'type':'choice','instructions':'choose','criteria':{'a':'one','b':'two'}}}}
    with pool_fixture(target=2,limit=4) as (pool,resources):
        runner_errors=[]
        def runner(spec,settings,cancel):
            from desktop_bridge.execution_budget import current
            try:
                with pool.lease(cancel,current().until) as resource:
                    return providers.call_codex(spec,settings,cancel,resource.cwd,session=resource.session)
            except Exception as error:
                runner_errors.append(type(error).__name__)
                raise
        runtime=Runtime(store,runner=runner,max_workers=2,max_pending=4)
        try:
            rid=str(uuid.uuid4())
            task=runtime.submit(body,caller,100,rid,protocol='decisions')
            assert task.done.wait(10)
            receipt=runtime.receipt(rid,caller)
            assert receipt['billing_status']=={'complete':not crash_second,'calls_started':2,
                                              'calls_completed':1 if crash_second else 2}
            assert receipt['billing']['usage']['cost']>0
            assert sum(r.session.sent['turn/start'] for r in resources)==2
            if crash_second:
                assert task.error and task.error.category=='provider_error' and 'result' not in receipt, runner_errors
            else:
                assert task.error is None and set(task.result['answers'])=={'a','b'}
                assert task.result['answers']['a']['noul']==.75
        finally:
            runtime.stop();store.close()


def test_pause_during_refill_discards_the_process_and_zero_resident_has_no_refill():
    started=threading.Event();release=threading.Event();resources=[]
    def factory(cancel,deadline):
        started.set();assert release.wait(2)
        resource=FakeResource(cancel,deadline);resources.append(resource);return resource
    pool=SingleUsePool(factory,lambda:'a',target=1,limit=1)
    try:
        assert started.wait(1)
        pool.pause();release.set()
        wait_for(lambda:pool.snapshot()['total']==0)
        assert resources[0].session.closed
        pool.configure(0,1);pool.resume();time.sleep(.1)
        assert len(resources)==1
    finally:pool.close()


def test_cleanup_failure_keeps_slot_counted_and_stops_refill():
    class BadResource:
        fail=True
        def healthy(self):return True
        def close(self):
            if self.fail:raise OSError('synthetic cleanup failure')
    resource=BadResource()
    pool=SingleUsePool(lambda *_:resource,lambda:'a',target=0,limit=1)
    try:
        with pytest.raises(OSError):
            with pool.lease(threading.Event(),time.monotonic()+1):pass
        assert pool.stop_event.is_set()
        assert pool.snapshot()['total']==pool.snapshot()['quarantined']==1
        with pytest.raises(BridgeError):
            with pool.lease(threading.Event(),time.monotonic()+1):pass
    finally:
        resource.fail=False;pool.close()


def test_stop_cancels_cold_startup_without_waiting_for_request_deadline():
    started=threading.Event()
    def factory(cancel,deadline):
        started.set()
        assert cancel.wait(5)
        raise BridgeError(499,'cancelled','synthetic')
    pool=SingleUsePool(factory,lambda:'a',target=0,limit=1)
    def request():
        with pytest.raises(BridgeError):
            with pool.lease(threading.Event(),time.monotonic()+90):pass
    with ThreadPoolExecutor(max_workers=1) as executor:
        future=executor.submit(request)
        assert started.wait(1)
        began=time.monotonic();pool.close()
        future.result(timeout=1)
        assert time.monotonic()-began<1 and not pool.entries


def test_waiting_request_takes_free_capacity_before_background_refill():
    acquired=threading.Event();release=threading.Event();threads=[]
    def factory(cancel,deadline):
        resource=FakeResource(cancel,deadline)
        resource.factory_thread=threading.current_thread().name
        return resource
    pool=SingleUsePool(factory,lambda:'a',target=1,limit=1)
    def request():
        with pool.lease(threading.Event(),time.monotonic()+5) as resource:
            threads.append(resource.factory_thread)
            acquired.set();assert release.wait(2)
    try:
        wait_for(lambda:pool.snapshot()['idle']==1)
        with ThreadPoolExecutor(max_workers=1) as executor:
            with pool.lease(threading.Event(),time.monotonic()+5):
                future=executor.submit(request)
                wait_for(lambda:pool.snapshot()['waiting_leases']==1)
            assert acquired.wait(2)
            assert threads[0]!='warm-cli-pilot'
            assert pool.snapshot()['peak']==1
            release.set();future.result(timeout=2)
    finally:
        release.set();pool.close()


def test_pool_default_is_zero_resident():
    pool=SingleUsePool(lambda *_:pytest.fail('must opt into prewarming'),lambda:'a')
    try:
        time.sleep(.1)
        assert pool.snapshot()['total']==0 and pool.target==0
    finally:pool.close()


def test_cold_provider_evicts_idle_without_exceeding_shared_budget(monkeypatch):
    from desktop_bridge.execution_budget import Budget, scope
    with pool_fixture(target=1, limit=1) as (pool, resources):
        wait_for(lambda:pool.snapshot()['idle']==1)
        idle=resources[0]
        def claude(spec, settings, cancel, cwd):
            assert pool.snapshot()['total']==pool.snapshot()['active']==1
            assert idle.session.closed and idle.session.sent['turn/start']==0
            return 'cold',{},'stop','synthetic'
        monkeypatch.setattr(providers,'call_claude',claude)
        class Settings:
            cli_pool=pool
            def get(self,name):return 2
        spec=spec_for('synthetic');spec.model['provider']='claude'
        budget=Budget(time.monotonic()+3,threading.Event())
        with scope(budget):
            assert providers.infer(spec,Settings(),budget.cancel)[0]=='cold'
        assert budget.leases=={'cold_starts':1}
        assert pool.snapshot()['peak']==1


def test_runtime_real_infer_path_records_warm_chat_and_each_decision(tmp_path,monkeypatch):
    import json
    import uuid
    from desktop_bridge.service import Runtime
    from desktop_bridge.store import Store
    monkeypatch.setattr('desktop_bridge.service.sys.platform','darwin')
    monkeypatch.setattr(providers,'inference_status',lambda *_:{'ready':True})
    resources=[]
    def resource(settings,cancel,deadline):
        value=FakeResource(cancel,deadline);resources.append(value);return value
    monkeypatch.setattr('desktop_bridge.warm_runtime.CodexResource',resource)
    store=Store(tmp_path);store.set('inference_resident',2)
    store.set('inference_workers',2);store.set('inference_pending',2)
    kid,key=store.create_key('synthetic');caller=store.authenticate(key)
    rt=Runtime(store)
    try:
        bodies=[('chat',{'model':'openai/gpt-6-astra','messages':[{'role':'user','content':'unique-marker'}]}),
                ('decisions',{'model':'openai/gpt-6-astra','state':'synthetic',
                 'questions':{n:{'type':'noul','instructions':'Synthetic?'} for n in ('a','b')}})]
        for protocol,body in bodies:
            wait_for(lambda:rt.cli_pool.snapshot()['idle']==2)
            rid=str(uuid.uuid4());task=rt.submit(body,caller,20,rid,protocol=protocol)
            assert task.done.wait(5)
            assert task.error is None, task.error.category if task.error else None
            receipt=rt.receipt(rid,caller)
            expected=1 if protocol=='chat' else 2
            assert receipt['execution']=={'warm_hits':expected,'cold_starts':0}
            assert receipt['billing_status']=={'complete':True,'calls_started':expected,'calls_completed':expected}
        assert sum(r.session.sent['turn/start'] for r in resources)==3
        assert all(r.session.sent['turn/start']<=1 for r in resources)
        store.set('accepting',False)
        rt.configure_capacity(2,2,0)
        wait_for(lambda:rt.cli_pool.snapshot()['total']==0)
        store.set('accepting',True)
        wait_for(lambda:not rt.cli_pool.paused)
        task=rt.submit(bodies[0][1],caller,20,str(uuid.uuid4()))
        assert task.done.wait(5) and task.error is None
        row=store.request(task.id,kid)
        assert row['warm_hits']==0 and row['cold_starts']==1
        assert rt.cli_pool.snapshot()['peak']<=2
        assert 'unique-marker' not in json.dumps(row)
    finally:
        rt.stop();store.close()
    assert all(r.session.closed and not Path(r.cwd).exists() for r in resources)


@pytest.mark.parametrize('resident',[-1,3,True,1.5])
def test_runtime_resident_validation_before_mutation(tmp_path,resident):
    from desktop_bridge.service import Runtime
    from desktop_bridge.store import Store
    store=Store(tmp_path);store.set('accepting',False)
    rt=Runtime(store,lambda *_:None,max_workers=2,max_pending=2)
    try:
        with pytest.raises(ValueError):rt.configure_capacity(2,2,resident)
        assert store.get('inference_resident')==0 and rt.max_workers==2
    finally:rt.stop();store.close()


def test_paused_runtime_can_drain_already_accepted_calls_without_refill():
    with pool_fixture(target=1,limit=1) as (pool,resources):
        wait_for(lambda:pool.snapshot()['idle']==1)
        pool.pause()
        before=len(resources)
        with pool.lease(threading.Event(),time.monotonic()+3,allow_paused=True) as resource:
            assert not getattr(resource,'warm_hit',False)
            assert pool.snapshot()['total']==1
        time.sleep(.1)
        assert len(resources)==before+1 and pool.snapshot()['total']==0
