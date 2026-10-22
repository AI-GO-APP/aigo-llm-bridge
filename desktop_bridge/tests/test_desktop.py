import json
import os
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

from desktop_bridge.store import Store
from desktop_bridge.service import Runtime,ApiServer
from desktop_bridge.contract import validate
from desktop_bridge.errors import BridgeError


def request(api,key,body=None,path="/api/v1/chat/completions"):
    req=urllib.request.Request(f"http://127.0.0.1:{api.port}"+path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req,timeout=10) as r:return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())


@pytest.fixture
def system(tmp_path):
    store=Store(tmp_path)
    _,key=store.create_key("test")
    calls=[]
    def runner(spec,settings,cancel):
        calls.append(spec)
        return "PONG",{"prompt_tokens":10,"completion_tokens":2},"stop"
    runtime=Runtime(store,runner); api=ApiServer(runtime,0); api.start()
    yield store,runtime,api,key,calls
    runtime.stop(); api.stop(); store.close()


BASE={"messages":[{"role":"user","content":"SYNTHETIC_REQUEST_CONTENT_97462"}]}


def test_standard_paths_and_metadata(system):
    store,rt,api,key,calls=system
    for path in ("/api/v1/chat/completions","/v1/chat/completions"):
        status,body=request(api,key,BASE,path)
        assert status==200 and body["choices"][0]["message"]["content"]=="PONG"
        assert body["system_fingerprint"] is None and body["usage"]["total_tokens"]==12
        assert body['usage']['cost']==0.000014
        assert "x_bridge" not in body
    assert len(calls)==2
    assert request(api,key,path="/api/v1/models")[0]==200
    for path in store.directory.iterdir():
        if path.is_file():
            assert b"SYNTHETIC_REQUEST_CONTENT_97462" not in path.read_bytes()
            assert key.encode() not in path.read_bytes()
            assert b"PONG" not in path.read_bytes()


@pytest.mark.parametrize("field,value",[("temperature",.1),("max_tokens",10),("stream",True),("tools",[]),
    ("tool_choice","auto"),("seed",1),("top_p",.9),("provider",{"order":["other"]}),("plugins",[]),("unknown",True)])
def test_unsupported_explicit_and_no_inference(system,field,value):
    store,rt,api,key,calls=system
    status,body=request(api,key,{**BASE,field:value})
    assert status==400 and body["error"]["metadata"]["error_type"]=="unsupported_parameter"
    assert calls==[]
    assert store.logs()[0]["status"]=="rejected"


@pytest.mark.parametrize("body",[{}, {"messages":[]},{"messages":None},{**BASE,"model":None},
    {**BASE,"stream":"false"},{**BASE,"reasoning_effort":[]},
    {"messages":[{"role":[],"content":"a"}]},
    {**BASE,"response_format":{"type":"json_schema","json_schema":{"name":"x","schema":{},"strict":"yes"}}}])
def test_invalid_types_are_400(system,body):
    _,_,api,key,calls=system
    assert request(api,key,body)[0]==400
    assert not calls


def test_nullable_sampling_is_absent(system):
    store,rt,api,key,calls=system
    assert request(api,key,{**BASE,"temperature":None,"max_tokens":None})[0]==200


def test_key_scope_revoke_rotate_restart(tmp_path):
    s=Store(tmp_path); kid,key=s.create_key("stable",["codex"],15)
    s.close();s=Store(tmp_path)
    assert s.authenticate(key)["id"]==kid
    with pytest.raises(BridgeError) as error:validate({**BASE,'model':'anthropic/claude-haiku-4.5'},s,s.authenticate(key))
    assert error.value.status==403
    new_id,new_key=s.rotate(kid)
    assert s.authenticate(key) is None and s.authenticate(new_key)["id"]==new_id
    s.revoke(new_id);assert s.authenticate(new_key) is None
    s.close()


def test_async_job_owner_and_memory_expiry(system):
    s,rt,api,key,_=system
    status,body=request(api,key,BASE,"/bridge/v1/jobs")
    assert status==202
    task=rt.tasks[body["id"]];assert task.done.wait(5)
    result=request(api,key,path="/bridge/v1/jobs/"+task.id)[1]["result"]
    assert result['object']=='chat.completion' and result['usage']['cost']==0.000014
    metadata=s.request(task.id,task.key_id)
    assert metadata['cost_usd']==result['usage']['cost'] and metadata['pricing_model']==result['model']=='openai/gpt-6-astra'
    _,other=s.create_key("other")
    assert request(api,other,path="/bridge/v1/jobs/"+task.id)[0]==404
    task.completed=time.time()-601
    assert request(api,key,path="/bridge/v1/jobs/"+task.id)[1]["status"]=="expired"


def test_restart_does_not_replay_or_store_payload(tmp_path):
    s=Store(tmp_path);kid,key=s.create_key("key")
    s.insert_request({"id":"a"*32,"key_id":kid,"status":"running","created_ts":time.time()})
    s.close();s=Store(tmp_path)
    assert s.request("a"*32,kid)["status"]=="interrupted"
    rt=Runtime(s)
    assert rt.get_job("a"*32,s.authenticate(key))["status"]=="interrupted"
    rt.stop();s.close()


def test_metadata_allowlist_and_export(tmp_path):
    s=Store(tmp_path)
    with pytest.raises(ValueError):s.insert_request({"id":"a","messages":"secret"})
    s.insert_request({"id":"a","created_ts":time.time()-40*86400,"status":"completed"})
    s.prune();assert not s.logs()
    s.insert_request({"id":"b","created_ts":time.time(),"status":"completed"})
    s.export(tmp_path/"metadata.csv")
    assert "messages" not in (tmp_path/"metadata.csv").read_text(encoding="utf-8-sig")
    s.prune(all_finished=True);assert not s.logs();s.close()


def test_revocation_cancels_owned_tasks_only(tmp_path):
    s=Store(tmp_path);kid,key=s.create_key("key");kid2,key2=s.create_key("key2")
    started=threading.Event()
    def wait(spec,settings,cancel):
        started.set();assert cancel.wait(5)
        raise BridgeError(499,"cancelled","Cancelled")
    rt=Runtime(s,wait)
    task=rt.submit(BASE,s.authenticate(key),100);assert started.wait(5)
    rt.cancel_key(kid2);assert not task.cancel.is_set()
    s.revoke(kid);rt.cancel_key(kid);assert task.done.wait(5)
    assert s.request(task.id,kid)["status"]=="cancelled"
    rt.stop();s.close()


def test_response_format_failure_is_not_success(system):
    s,rt,api,key,calls=system
    status,result=request(api,key,{**BASE,"response_format":{"type":"json_object"}})
    assert status==502 and result["error"]["metadata"]["error_type"]=="invalid_structured_output"


def test_claude_history_rejected_and_codex_preserved(system):
    s,rt,api,key,calls=system
    history={"messages":[{"role":"user","content":"a"},{"role":"assistant","content":"b"},{"role":"user","content":"c"}]}
    assert request(api,key,{**history,'model':'anthropic/claude-haiku-4.5'})[0]==400
    assert request(api,key,{**history,"model":"openai/gpt-6-astra"})[0]==200
    assert len(calls[-1].messages)==3


@pytest.mark.parametrize("ref",["$ref","$dynamicRef"])
def test_remote_schema_references_are_rejected(system,ref):
    s,rt,api,key,calls=system
    body={**BASE,"response_format":{"type":"json_schema","json_schema":{"name":"blocked",
          "schema":{"type":"object","properties":{"value":{ref:"https://example.invalid/schema"}}}}}}
    assert request(api,key,body)[0]==400
    assert not calls


@pytest.mark.skipif(os.name!="nt",reason="Windows native instance event")
def test_second_instance_requests_existing_ui(tmp_path):
    from desktop_bridge.windows import Instance
    first=Instance(tmp_path); second=Instance(tmp_path)
    try:
        assert first.primary and not second.primary
        assert not first.requested()
        second.notify(); assert first.requested()
        assert not first.requested()
    finally: second.close(); first.close()


def test_cli_attach_preserves_live_requests_and_existing_logs(tmp_path):
    original=Store(tmp_path)
    original.insert_request({"id":"running","status":"running","created_ts":time.time()})
    original.insert_request({"id":"old","status":"completed","created_ts":time.time()-40*86400})
    attached=Store(tmp_path,startup=False)
    assert {r["id"]:r["status"] for r in attached.logs()}=={"running":"running","old":"completed"}
    attached.close(); original.close()
    restarted=Store(tmp_path)
    assert {r["id"]:r["status"] for r in restarted.logs()}=={"running":"interrupted"}
    restarted.close()
