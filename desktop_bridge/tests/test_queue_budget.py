"""Admission, lifecycle and safety regressions; no subscription or external traffic."""
import json
import random
import threading
import time
import uuid
import gc
import weakref
import sqlite3
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pytest
from jsonschema import Draft202012Validator

from desktop_bridge import schema_guard
from desktop_bridge.decision_contract import output_schema
from desktop_bridge.decisions import typed_output
from desktop_bridge.errors import BridgeError
from desktop_bridge.execution_budget import Budget, TIMING_COLUMNS, scope
from desktop_bridge.service import Runtime, ApiServer
from desktop_bridge.store import Store

CHAT={'model':'openai/gpt-6-astra','messages':[{'role':'user','content':'synthetic'}]}
DECISION={'model':'anthropic/claude-haiku-4.5','state':'synthetic',
          'questions':{'q':{'type':'noul','instructions':'Synthetic?'}}}


def test_32_running_32_queued_share_capacity_and_cancel_frees_before_dequeue(tmp_path):
    store=Store(tmp_path);_,token=store.create_key('synthetic');caller=store.authenticate(token)
    release=threading.Event();entered=threading.Event();lock=threading.Lock();calls=[]
    def runner(spec,*_):
        with lock:
            calls.append(spec)
            if len(calls)==32:entered.set()
        assert release.wait(5)
        return ('{"noul":0.9}' if spec.schema else 'OK'),{'prompt_tokens':2,'completion_tokens':1},'stop'
    rt=Runtime(store,runner,max_workers=32,max_pending=64)
    api=ApiServer(rt,0);api.start()
    try:
        tasks=[rt.submit(DECISION if i%2 else CHAT,caller,20,
                         protocol='decisions' if i%2 else 'chat') for i in range(64)]
        assert entered.wait(2)
        assert rt.capacity()['running_requests']==32 and rt.capacity()['queued_requests']==32
        latencies=[]
        for _ in range(20):
            began=time.monotonic()
            with urllib.request.urlopen(f'http://127.0.0.1:{api.port}/health',timeout=1) as response:
                assert json.load(response)['max_execution_workers']==32
            latencies.append(time.monotonic()-began)
        assert sorted(latencies)[18]<1
        with pytest.raises(BridgeError) as error:rt.submit(CHAT,caller,20)
        assert error.value.status==429
        tasks[-1].cancel.set()
        assert tasks[-1].done.wait(.9) and tasks[-1].error.status==499
        assert len(calls)==32
        replacement=rt.submit(CHAT,caller,20)
        release.set()
        assert all(t.done.wait(5) for t in [*tasks,replacement])
        assert len(calls)==64
        assert store.request(tasks[-1].id,caller['id'])['calls_started']==0
        assert rt.capacity()['queued_requests']==rt.capacity()['running_requests']==0
    finally:release.set();rt.stop();api.stop();store.close()


@pytest.mark.parametrize('cause',['deadline','revoke','cancel'])
def test_terminal_queued_jobs_release_prompt_and_capacity_while_first_still_runs(tmp_path,cause):
    store=Store(tmp_path);kid,key=store.create_key('synthetic');caller=store.authenticate(key)
    _,other_key=store.create_key('other');other=store.authenticate(other_key)
    release=threading.Event();started=threading.Event();calls=[]
    def runner(*_):
        calls.append(1);started.set();assert release.wait(4)
        return 'OK',{'prompt_tokens':2,'completion_tokens':1},'stop'
    rt=Runtime(store,runner,max_workers=1,max_pending=2)
    try:
        first=rt.submit(CHAT,other,20);assert started.wait(1)
        request_id=str(uuid.uuid4())
        task=rt.submit(CHAT,caller,20,request_id)
        # This test exercises a queued expiry. A tiny admission deadline may
        # expire during validation on a loaded runner, where queue_wait is
        # correctly unobserved/null. Expire only after verifying queue entry.
        assert task.phase=='queued'
        if cause=='deadline':task.budget.until=time.monotonic()
        if cause=='revoke':store.revoke(kid)
        if cause=='cancel':task.cancel.set()
        assert task.done.wait(.9)
        assert task.error.status=={'deadline':408,'revoke':401,'cancel':499}[cause]
        assert not rt.waiting and len(calls)==1
        receipt=rt.receipt(request_id,caller)
        assert receipt['billing_status']=={'complete':True,'calls_started':0,'calls_completed':0}
        assert 'billing' not in receipt
        row=store.request(task.id,kid)
        assert row['total_ms']>=0 and row['queue_wait_ms']>=0
        replacement=rt.submit(CHAT,other,20)
        release.set();assert first.done.wait(3) and replacement.done.wait(3)
        assert len(calls)==2
    finally:release.set();rt.stop();store.close()


def test_fifo_dedupe_and_stop_clean_queued_without_execution(tmp_path):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    release=threading.Event();started=threading.Event();calls=[]
    def runner(spec,*_):
        calls.append(spec.messages[0]['parts'][0]['text']);started.set()
        assert release.wait(3)
        return 'OK',{'prompt_tokens':1,'completion_tokens':1},'stop'
    rt=Runtime(store,runner,max_workers=1,max_pending=4)
    try:
        first=rt.submit(CHAT,caller,20);assert started.wait(1)
        tasks=[]
        for i in range(3):
            body={**CHAT,'messages':[{'role':'user','content':str(i)}]}
            rid=str(uuid.uuid4());task=rt.submit(body,caller,20,rid);tasks.append(task)
            assert rt.submit(body,caller,20,rid) is task
        release.set();assert all(t.done.wait(3) for t in [first,*tasks])
        assert calls==['synthetic','0','1','2']
    finally:release.set();rt.stop();store.close()


def test_stop_cancels_queue_without_dequeue_and_joins_owned_workers(tmp_path):
    store=Store(tmp_path);kid,key=store.create_key('synthetic');caller=store.authenticate(key)
    entered=threading.Event();calls=[]
    def runner(spec,settings,cancel):
        calls.append(1);entered.set();assert cancel.wait(3)
        raise BridgeError(499,'cancelled','Synthetic cancellation.')
    rt=Runtime(store,runner,max_workers=1,max_pending=3)
    try:
        first=rt.submit(CHAT,caller,20);assert entered.wait(1)
        queued=[rt.submit(CHAT,caller,20) for _ in range(2)]
        rt.stop()
        assert len(calls)==1 and first.done.is_set()
        assert all(t.done.is_set() and t.error.status==499 for t in queued)
        assert all(store.request(t.id,kid)['calls_started']==0 for t in queued)
        assert store.request(first.id,kid)['billing_complete']==0
        assert not rt.monitor.is_alive() and not any(t.is_alive() for t in rt.worker_threads)
    finally:rt.stop();store.close()


def test_worker_start_failure_never_leaves_a_runnable_terminal_spec(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    calls=[];rt=Runtime(store,lambda *_:calls.append('must not execute'),max_workers=1,max_pending=1)
    real_start=threading.Thread.start
    def fail_inference(thread):
        if thread.name.startswith('bridge-inference-'):raise RuntimeError('synthetic thread limit')
        return real_start(thread)
    monkeypatch.setattr(threading.Thread,'start',fail_inference)
    try:
        with pytest.raises(RuntimeError):rt.submit(CHAT,caller,20)
        assert not rt.waiting and not calls
        assert rt.capacity()['queued_requests']==0
        assert next(iter(rt.tasks.values())).done.is_set()
        assert rt.slots.acquire(blocking=False)
        rt.slots.release()
    finally:rt.stop();store.close()


def test_terminal_receipt_write_failure_releases_capacity_without_false_success(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    rt=Runtime(store,lambda *_:('OK',{'prompt_tokens':1,'completion_tokens':1},'stop'),max_workers=1,max_pending=1)
    update=store.update_request;failed=[]
    def fail_terminal_once(rid,**changes):
        if 'total_ms' in changes and not failed:
            failed.append(True);raise sqlite3.OperationalError('synthetic disk failure')
        return update(rid,**changes)
    monkeypatch.setattr(store,'update_request',fail_terminal_once)
    try:
        task=rt.submit(CHAT,caller,20,str(uuid.uuid4()));assert task.done.wait(2)
        assert task.result is None and task.error.status==503
        assert task.error.category=='metadata_unavailable'
        assert rt.capacity()['running_requests']==0
        # Known usage survived; terminal write was not silently invented.
        assert store.request(task.id,caller['id'])['cost_usd'] is not None
        next_task=rt.submit(CHAT,caller,20);assert next_task.done.wait(2)
        assert next_task.error is None
    finally:rt.stop();store.close()


def test_stop_racing_validation_cannot_enqueue_after_scheduler_shutdown(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    validated=threading.Event();release=threading.Event()
    rt=Runtime(store,lambda *_:pytest.fail('Stop must prevent inference.'),max_workers=1,max_pending=1)
    real=rt.check_execution
    def hold_after_first_check(*args):
        real(*args)
        if not validated.is_set():
            validated.set();assert release.wait(3)
    monkeypatch.setattr(rt,'check_execution',hold_after_first_check)
    try:
        with ThreadPoolExecutor(max_workers=2) as clients:
            submit=clients.submit(rt.submit,CHAT,caller,20)
            assert validated.wait(1)
            stop=clients.submit(rt.stop)
            until=time.monotonic()+1
            while not rt.stopped and time.monotonic()<until:time.sleep(.01)
            assert rt.stopped
            release.set();task=submit.result(2);stop.result(2)
            assert task.done.is_set() and task.error.status==499 and not rt.waiting
    finally:release.set();rt.stop();store.close()


def test_schema_admission_reservation_precedes_expensive_validation(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    entered=threading.Event();release=threading.Event()
    rt=Runtime(store,lambda *_:('OK',{'prompt_tokens':1,'completion_tokens':1},'stop'),max_workers=1,max_pending=1)
    real=rt.validate_request
    def blocked(*args):
        entered.set();assert release.wait(10)
        return real(*args)
    monkeypatch.setattr(rt,'validate_request',blocked)
    try:
        with ThreadPoolExecutor(max_workers=1) as clients:
            # This tests reservation ordering, independent of OS thread scheduling.
            # Deadline exhaustion has dedicated tests below.
            future=clients.submit(rt.submit,CHAT,caller,20)
            try:
                assert entered.wait(5)
                with pytest.raises(BridgeError) as error:rt.submit(CHAT,caller,20)
                assert error.value.category=='queue_full'
            finally:release.set()
            task=future.result(5);assert task.done.wait(5)
    finally:release.set();rt.stop();store.close()


def test_schema_capacity_wait_and_process_use_remaining_request_budget(monkeypatch):
    occupied=threading.BoundedSemaphore(1);occupied.acquire()
    monkeypatch.setattr(schema_guard,'CAPACITY',occupied)
    started=time.monotonic();budget=Budget(started+.12,threading.Event())
    with scope(budget),pytest.raises(BridgeError) as error:
        schema_guard.check_schemas([{'type':'object'}],'response_format')
    assert error.value.status==408 and time.monotonic()-started<1
    assert budget.metadata()['schema_wait_ms']>=50
    assert not occupied.acquire(blocking=False)
    occupied.release()
    # A malicious output regex still executes only in the disposable child.
    started=time.monotonic()
    with scope(Budget(started+.4,threading.Event())),pytest.raises(BridgeError) as error:
        schema_guard.validate_instances([[{'type':'string','pattern':'^(a+)+$'},'a'*32+'!']])
    assert error.value.status==408 and time.monotonic()-started<1.4


@pytest.mark.parametrize('metadata',['models','pricing'])
def test_shared_metadata_lock_wait_obeys_request_deadline_without_inference(tmp_path,metadata):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    rt=Runtime(store,lambda *_:pytest.fail('Expired metadata wait must not infer.'))
    lock=rt.models.lock if metadata=='models' else rt.pricing.lock
    lock.acquire()
    body={**CHAT,'model':'openai/synthetic-unregistered'} if metadata=='models' else CHAT
    began=time.monotonic()
    try:
        with ThreadPoolExecutor(max_workers=1) as clients:
            task=clients.submit(rt.submit,body,caller,20,deadline=time.time()+.12).result(1)
            assert task.done.wait(.9) and task.error.status==408
            assert time.monotonic()-began<1
            assert store.request(task.id,caller['id'])['calls_started']==0
    finally:lock.release();rt.stop();store.close()


def test_auth_status_timeout_does_not_hide_expired_request_budget(monkeypatch):
    import subprocess
    import sys
    from desktop_bridge import providers
    monkeypatch.setattr(providers,'executable',lambda *_:sys.executable)
    def timeout(command,**kwargs):
        assert kwargs['timeout']<=.12
        time.sleep(kwargs['timeout']+.01)
        raise subprocess.TimeoutExpired(command,kwargs['timeout'])
    monkeypatch.setattr(providers.subprocess,'run',timeout)
    with scope(Budget(time.monotonic()+.12,threading.Event())),pytest.raises(BridgeError) as error:
        providers.status('claude',{})
    assert error.value.status==408


def test_capacity_migration_and_atomic_reconfiguration(tmp_path):
    store=Store(tmp_path);store.set('inference_workers',2)
    assert store.get('inference_pending')==2
    rt=Runtime(store)
    try:
        with pytest.raises(ValueError):rt.configure_capacity(1,64)
        store.set('accepting',False)
        for pair in [(0,64),(True,64),(2,1),(1,65),(1,False)]:
            with pytest.raises(ValueError):rt.configure_capacity(*pair)
        assert rt.max_workers==rt.max_pending==2
        store.db.execute("create trigger fail_pending before insert on settings when new.name='inference_pending' begin select raise(abort,'synthetic failure'); end")
        store.db.commit()
        with pytest.raises(sqlite3.IntegrityError):rt.configure_capacity(1,64)
        assert (store.get('inference_workers'),store.get('inference_pending'))==(2,2)
        assert rt.max_workers==rt.max_pending==2
        store.db.execute('drop trigger fail_pending');store.db.commit()
        rt.configure_capacity(1,64)
        assert (store.get('inference_workers'),store.get('inference_pending'))==(1,64)
        assert rt.capacity()['max_execution_workers']==1
    finally:rt.stop();store.close()
    store=Store(tmp_path);rt=Runtime(store)
    try:assert (rt.max_workers,rt.max_pending)==(1,64)
    finally:rt.stop();store.close()


def test_metrics_are_numeric_allowlist_and_old_rows_stay_null(tmp_path):
    store=Store(tmp_path);kid,key=store.create_key('synthetic')
    store.insert_request({'id':'old','key_id':kid,'status':'completed'})
    rt=Runtime(store,lambda *_:('OK',{'prompt_tokens':1,'completion_tokens':1},'stop'))
    try:
        task=rt.submit(CHAT,store.authenticate(key),20);assert task.done.wait(2)
        row=store.request(task.id,kid)
        assert all(row[k] is None or type(row[k]) is int and row[k]>=0 for k in TIMING_COLUMNS)
        assert row['validation_ms'] is not None and row['total_ms'] is not None
        assert row['cli_ready_ms'] is None
        assert all(store.request('old',kid)[k] is None for k in TIMING_COLUMNS)
        assert 'synthetic' not in json.dumps(row)
    finally:rt.stop();store.close()


def test_cancelled_large_queued_spec_is_not_retained_by_executor_or_exception(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');caller=store.authenticate(key)
    release=threading.Event();started=threading.Event();references=[]
    def runner(*_):
        started.set();assert release.wait(3)
        return 'OK',{'prompt_tokens':1,'completion_tokens':1},'stop'
    rt=Runtime(store,runner,max_workers=1,max_pending=2);real=rt.validate_request
    def observe(*args):
        spec=real(*args);references.append(weakref.ref(spec));return spec
    monkeypatch.setattr(rt,'validate_request',observe)
    try:
        rt.submit(CHAT,caller,20);assert started.wait(1)
        body={**CHAT,'messages':[{'role':'user','content':'S'*2_999_000}]}
        task=rt.submit(body,caller,2_999_100);del body
        task.cancel.set();assert task.done.wait(.9)
        gc.collect()
        assert references[-1]() is None and task.error.__traceback__ is None
        assert not rt.waiting
    finally:release.set();rt.stop();store.close()


def test_decisions_never_enter_generic_schema_guard(tmp_path,monkeypatch):
    monkeypatch.setattr(schema_guard,'run',lambda *_:pytest.fail('Fixed Decisions must not launch a schema child.'))
    store=Store(tmp_path);_,key=store.create_key('synthetic')
    rt=Runtime(store,lambda *_:('{"noul":0.9}',{'prompt_tokens':1,'completion_tokens':1},'stop'))
    try:
        task=rt.submit(DECISION,store.authenticate(key),20,protocol='decisions')
        assert task.done.wait(2) and task.error is None
        assert task.result['answers']['q']['noul']==.9
    finally:rt.stop();store.close()


def test_wall_clock_adjustment_does_not_change_admitted_monotonic_budget(tmp_path,monkeypatch):
    store=Store(tmp_path);_,key=store.create_key('synthetic');real_time=time.time
    def runner(spec,settings,cancel):
        monkeypatch.setattr('desktop_bridge.service.time.time',lambda:real_time()+3600)
        assert settings.get('timeout_s')>80
        return 'OK',{'prompt_tokens':1,'completion_tokens':1},'stop'
    rt=Runtime(store,runner)
    try:
        task=rt.submit(CHAT,store.authenticate(key),20);assert task.done.wait(2)
        assert task.error is None and task.result is not None
    finally:rt.stop();store.close()


def test_fixed_typed_structures_match_jsonschema_on_deterministic_boundary_corpus():
    rng=random.Random(36)
    values=[None,True,False,'0',-1,0,.5,1,2,{},[],[0,1],[.5,.5]]
    for kind,count in [('noul',1),('choice',1),('choice',255),('score',2),('score',10)]:
        q={'type':kind,'criteria':list(range(count))}
        schema=output_schema(q);validator=Draft202012Validator(schema)
        field='noul' if kind=='noul' else 'probabilities'
        corpus=values+[{field:v} for v in values]
        corpus += [{field:[rng.choice([0,1,-1,.5,True,'0',None]) for _ in range(rng.randrange(count+2))]} for _ in range(100)]
        corpus += [{field:0 if kind=='noul' else [1/count]*count}]
        corpus += [{field:0 if kind=='noul' else [1/count]*count,'extra':None}]
        for value in corpus:
            try:typed_output(value,q);valid=True
            except (ValueError,TypeError,OverflowError):valid=False
            assert valid==validator.is_valid(value)
