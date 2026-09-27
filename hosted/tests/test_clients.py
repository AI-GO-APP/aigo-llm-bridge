"""clients/ 的三種呼叫端,對一個真的在跑的 Bridge(記憶體存放 + 假雲端後端)測。

- clients/python/aigo_bridge.py(Hosted App 或任何伺服器程式)
- clients/custom-app/bridge_block.py(貼進 Server Action 的區塊;ctx.http.call 以 urllib 模擬)
- examples/hosted-app-caller/main.py(用 Python 客戶端的 FastAPI 範例)
"""

import importlib.util
import json
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

from test_app import KEY, FakeProvider, make

ROOT = Path(__file__).resolve().parents[2]
CLOUD = "openrouter/vendor/model-x"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_mod = load("aigo_bridge", ROOT / "clients" / "python" / "aigo_bridge.py")


@pytest.fixture(scope="module")
def bridge_url():
    app, providers = make(auto_cloud_model=CLOUD, source_keys={"APP": KEY})
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    url = f"http://127.0.0.1:{port}"
    url_providers = (url, app, providers)
    yield url_providers
    server.should_exit = True
    thread.join(timeout=5)


# ── Python 客戶端 ──────────────────────────────────────────────────────────
def test_python_client_priority_chat_and_stream(bridge_url):
    url, app, providers = bridge_url
    bridge = client_mod.BridgeClient(url, key=KEY)
    user = "py-user"
    assert bridge.get_priority(user)["priority"] is None
    with pytest.raises(client_mod.BridgeError) as err:
        bridge.chat([{"role": "user", "content": "hi"}], user=user)
    assert err.value.code == "priority_required" and err.value.status == 409

    bridge.set_priority(user, "local")          # 沒有 worker → 改用雲端,並註明
    reply = bridge.chat([{"role": "user", "content": "hi"}], user=user)
    assert reply.content == "echo:vendor/model-x"
    assert reply.priority == "local" and reply.fallback == {"from": "local/self", "reason": "no_worker_for_user"}

    events = list(bridge.stream([{"role": "user", "content": "hi"}], user=user))
    assert "".join(e.text for e in events if e.kind == "delta") == "ab"
    done = events[-1]
    assert done.kind == "done" and done.complete is True
    assert done.meta["fallback"] == {"from": "local/self", "reason": "no_worker_for_user"}


def test_python_client_hmac_and_errors(bridge_url):
    url, _, _ = bridge_url
    signed = client_mod.BridgeClient(url, key=KEY, source="APP")
    assert signed.get_priority("hmac-user")["priority"] is None
    wrong = client_mod.BridgeClient(url, key="nope", source="APP")
    with pytest.raises(client_mod.BridgeError) as err:
        wrong.get_priority("hmac-user")
    assert err.value.code == "bad_signature"
    with pytest.raises(client_mod.BridgeError) as err:
        signed.set_priority("hmac-user", "fastest")
    assert err.value.code == "bad_priority"
    code = signed.enrollment_code("hmac-user")
    assert len(code["code"]) == 9 and signed.computers("hmac-user") == []


# ── Server Action 區塊 ─────────────────────────────────────────────────────
class FakeHttp:
    """模擬 ctx.http.call:回 {"status", "data"},不回標頭(與平台實測一致)。"""

    def __init__(self, base):
        self.base, self.slugs = base, []

    def call(self, slug, path, method="GET", body=None, headers=None):
        self.slugs.append(slug)
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return {"status": resp.status, "data": json.loads(resp.read() or b"{}")}
        except urllib.error.HTTPError as exc:
            return {"status": exc.code, "data": json.loads(exc.read() or b"{}")}


class FakeCtx:
    def __init__(self, base, user):
        self.secrets = {"BRIDGE_KEY": KEY, "BRIDGE_PUBLIC_URL": base}
        self.user_id = user
        self.http = FakeHttp(base)
        self.params = {}


def test_custom_app_block(bridge_url):
    url, _, _ = bridge_url
    block = load("bridge_block", ROOT / "clients" / "custom-app" / "bridge_block.py")
    ctx = FakeCtx(url, "block-user")
    first = block.bridge_chat(ctx, [{"role": "user", "content": "hi"}])
    assert first["ok"] is False and first["code"] == "priority_required"
    assert block.bridge_get_priority(ctx)["priority"] is None
    assert block.bridge_set_priority(ctx, "cloud")["priority"] == "cloud"
    reply = block.bridge_chat(ctx, [{"role": "user", "content": "hi"}])
    assert reply["ok"] and reply["content"] == "echo:vendor/model-x"
    assert reply["priority"] == "cloud" and reply["fallback"] is None
    token = block.bridge_session_token(ctx)
    assert token["ok"] and token["base_url"] == url
    assert block.bridge_computers(ctx) == {"ok": True, "workers": []}
    assert set(ctx.http.slugs) == {"llm-bridge"}                  # 一律用字面 slug
    ctx.secrets = {}
    assert block.bridge_chat(ctx, [])["code"] == "not_configured"


# ── Hosted App 範例 ────────────────────────────────────────────────────────
def test_hosted_example(bridge_url, monkeypatch):
    url, _, _ = bridge_url
    monkeypatch.setenv("BRIDGE_URL", url)
    monkeypatch.setenv("BRIDGE_KEY", KEY)
    monkeypatch.setenv("INTERNAL_KEY", "internal-test")
    sys.path.insert(0, str(ROOT / "examples" / "hosted-app-caller"))
    try:
        example = load("hosted_example_main", ROOT / "examples" / "hosted-app-caller" / "main.py")
    finally:
        sys.path.pop(0)
    web = TestClient(example.app)
    who = {"X-Internal-Key": "internal-test", "X-User-Id": "hosted-user"}
    assert web.get("/priority").status_code == 401                  # 沒有可信的上游就不認身分
    assert web.get("/priority", headers=who).json()["priority"] is None
    r = web.post("/ask", json={"prompt": "hi"}, headers=who)
    assert r.status_code == 409 and r.json()["error"]["code"] == "priority_required"
    web.put("/priority", json={"priority": "local"}, headers=who)
    r = web.post("/ask", json={"prompt": "hi"}, headers=who)
    assert r.status_code == 200 and r.json()["fallback"]["reason"] == "no_worker_for_user"
    lines = [json.loads(ln[6:]) for ln in web.post("/ask/stream", json={"prompt": "hi"}, headers=who).text.split("\n")
             if ln.startswith("data: ")]
    assert "".join(e["text"] for e in lines if e["kind"] == "delta") == "ab"
    assert lines[-1]["kind"] == "done" and lines[-1]["complete"] is True
