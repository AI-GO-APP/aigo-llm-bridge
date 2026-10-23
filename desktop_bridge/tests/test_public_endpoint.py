import io
import json

from desktop_bridge.public_endpoint import PublicEndpoint, inspect
from desktop_bridge.store import Store
from desktop_bridge.handoff import integration


def test_old_worker_online_does_not_mean_new_routes_available(monkeypatch):
    seen=[]
    class Response(io.BytesIO):
        def __init__(self, value, status):
            super().__init__(json.dumps(value).encode()); self.status=status
    class Opener:
        def open(self, req, timeout):
            seen.append(req)
            return Response({'version':'0.3.4-relay','device_online':True},200) if req.full_url.endswith('/health') else Response({},404)
    monkeypatch.setattr('desktop_bridge.public_endpoint.urllib.request.build_opener',lambda *_:Opener())
    result=inspect('https://owner.example')
    assert result['online'] and result['worker_version']=='0.3.4-relay'
    assert all(r['state']=='unsupported' for r in result['routes'].values())
    assert len(seen)==5
    assert all(not req.has_header('Authorization') for req in seen)
    assert all(req.data in (None,b'{}') for req in seen)


def test_evidence_expires_and_cannot_follow_a_changed_origin(tmp_path,monkeypatch):
    store=Store(tmp_path);store.set('public_url','https://owner.example')
    status=PublicEndpoint(store)
    assert status.snapshot()['state']=='unchecked'
    now=[1000.]
    monkeypatch.setattr('desktop_bridge.public_endpoint.time.time',lambda:now[0])
    monkeypatch.setattr('desktop_bridge.public_endpoint.inspect',lambda _: {'checked_at':now[0], 'worker_version':'0.9.0-relay','online':True,'routes':{n:{'state':'reachable','http_status':401} for n in ('decisions','capabilities','refresh','probe')}})
    assert status.check()['state']=='routes_reachable'
    status.observe('https://owner.example/api/v1','openai/gpt-6-astra','decisions',{'success':True,'http_status':200,'cost_usd':.01})
    assert status.snapshot()['tests'][0]['protocol']=='decisions'
    now[0]+=301
    assert status.snapshot()['state']=='unchecked' and status.snapshot()['stale']
    store.set('public_url','https://new-owner.example')
    result=status.snapshot()
    assert result['state']=='unchecked' and not result['tests'] and not result.get('checked_at')
    store.close()


def test_handoff_states_public_gap_instead_of_promising_deployment(tmp_path):
    store=Store(tmp_path);store.set('public_url','https://owner.example')
    assert '不能當成外網已驗證' in integration(store)['prompt']
    info=integration(store,public_status={'state':'needs_update','worker_version':'0.3.4-relay','checked_at':1000,'tests':[]})
    assert 'Decisions／模型探索尚不可交付' in info['prompt']
    assert info['public_status']['state']=='needs_update'
    store.close()


def test_decisions_probe_requires_actual_model_and_cost_and_keeps_payload_out(monkeypatch):
    from desktop_bridge.connection_test import probe
    payload={'model':'synthetic/model','answers':{'blue':{'noul':.8}},'usage':{'cost':.01}}
    seen=[]
    class Response(io.BytesIO):
        status=200
    class Opener:
        def open(self,req,**_):
            seen.append(req)
            return Response(json.dumps(payload).encode())
    monkeypatch.setattr('desktop_bridge.connection_test.urllib.request.build_opener',lambda *_:Opener())
    result=probe('https://owner.example/api/v1','synthetic/model','test-secret','decisions')
    assert result['success'] and result['cost_usd']==.01
    assert seen[0].full_url=='https://owner.example/api/alpha/decisions'
    assert set(json.loads(seen[0].data))=={'model','state','questions'}
    assert 'answers' not in result and 'test-secret' not in json.dumps(result)
    payload['model']='different-model'
    assert not probe('https://owner.example/api/v1','synthetic/model','test-secret','decisions')['success']
