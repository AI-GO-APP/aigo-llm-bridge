import io
import json
import threading
import time
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import urllib.error
import urllib.request

import pytest

from desktop_bridge import providers
from desktop_bridge.relay import Relay,read_cloud
from desktop_bridge.schema_guard import check_schemas,validate_instances
from desktop_bridge.errors import BridgeError
from desktop_bridge.store import Store


def test_relay_never_forwards_credentials_to_redirect_target(tmp_path):
    received=[]
    class Target(BaseHTTPRequestHandler):
        def log_message(self,*_):pass
        def do_GET(self):received.append(self.headers.get('Authorization'));self.send_response(200);self.end_headers()
    target=ThreadingHTTPServer(('127.0.0.1',0),Target)
    class Redirect(Target):
        def do_POST(self):
            self.send_response(302);self.send_header('Location',f'http://127.0.0.1:{target.server_port}/');self.end_headers()
    source=ThreadingHTTPServer(('127.0.0.1',0),Redirect)
    for server in (source,target):threading.Thread(target=server.serve_forever,daemon=True).start()
    store=Store(tmp_path);relay=Relay(store,0)
    try:
        req=urllib.request.Request(f'http://127.0.0.1:{source.server_port}/',data=b'{}',headers={'Authorization':'Bearer synthetic-device'})
        with pytest.raises(urllib.error.HTTPError) as error:relay.cloud_opener.open(req,timeout=2)
        assert error.value.code==302 and received==[]
        with pytest.raises(ValueError):read_cloud(io.BytesIO(b'x'*12),10)
        with pytest.raises(ValueError):read_cloud(io.BytesIO(b'[]'))
    finally:
        relay.pool.shutdown();store.close()
        for server in (source,target):server.shutdown();server.server_close()


def test_claude_dynamic_content_is_only_in_stdin(monkeypatch,tmp_path):
    system='synthetic-system-canary';schema={'type':'object','description':'synthetic-schema-canary'}
    captured={}
    class Child:
        proc=SimpleNamespace(returncode=0)
        def __init__(self,command,*_):captured['command']=command
        def communicate(self,payload,*_):
            captured['payload']=payload.decode()
            return json.dumps({'type':'result','result':'```json\n{}\n```','usage':{'input_tokens':1,'output_tokens':1},'modelUsage':{'test':{}}}).encode()
        def close(self):pass
    monkeypatch.setattr(providers,'Child',Child)
    monkeypatch.setattr(providers,'status',lambda *_:{'ready':True})
    monkeypatch.setattr(providers,'executable',lambda *_:'synthetic-cli')
    spec=SimpleNamespace(model={'native':'test'},system=system,schema=schema,effort=None,messages=[{'parts':[{'type':'text','text':'synthetic-user-canary'}]}])
    assert providers.call_claude(spec,{'timeout_s':10},threading.Event(),tmp_path)[0]=='{}'
    assert system in captured['payload'] and schema['description'] in captured['payload']
    assert all(marker not in ' '.join(captured['command']) for marker in (system,schema['description'],'synthetic-user-canary'))
    assert '--no-session-persistence' in captured['command'] and '--restricted' in captured['command']
    assert '--json-schema' not in captured['command']


def test_provider_environment_excludes_unrelated_credentials(monkeypatch):
    monkeypatch.setenv('CLOUDFLARE_API_TOKEN','synthetic');monkeypatch.setenv('AWS_SECRET_ACCESS_KEY','synthetic')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic');monkeypatch.setenv('CODEX_HOME','synthetic-home')
    value=providers.environment()
    assert not {'CLOUDFLARE_API_TOKEN','AWS_SECRET_ACCESS_KEY','OPENAI_API_KEY'}&value.keys()
    assert value['CODEX_HOME']=='synthetic-home'


@pytest.mark.parametrize('schema',[
    {'type':'object','$ref':'#'},
    {'type':'object','description':'x'*262145},
    {'type':'object','allOf':[{'type':'object'}]*9000},
])
def test_unbounded_schema_is_rejected_before_provider(schema):
    with pytest.raises(BridgeError) as error:check_schemas([schema],'response_format')
    assert error.value.category=='unsupported_parameter' and error.value.status==400


def test_schema_regex_cannot_hold_parent_process():
    schema={'type':'object','properties':{'value':{'type':'string','pattern':'^(a+)+$'}}}
    check_schemas([schema],'response_format')
    start=time.monotonic()
    assert not validate_instances([[schema,{'value':'a'*32+'!'}]])
    assert time.monotonic()-start<9
    assert validate_instances([[{'type':'object','properties':{'value':{'type':'integer'}}},{'value':4}]])
