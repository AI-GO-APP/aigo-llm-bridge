"""hosted-echo 的本機測試(不需網路):python -m pytest spikes/hosted-echo -q"""
import json
import os
import sys
from pathlib import Path

os.environ["SPIKE_KEY"] = "test-key"
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402

client = TestClient(main.app)
KEY = {"Authorization": "Bearer test-key"}


def test_health_is_open():
    r = client.get("/healthz")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_rejects_missing_and_wrong_credentials():
    assert client.post("/v1/chat/completions", json={}).status_code == 401
    assert client.post("/v1/chat/completions", json={}, headers={"Authorization": "Bearer nope"}).status_code == 401


def test_session_token_roundtrip_and_scope():
    tok = client.post("/bridge/session", json={"user": "a@example.com"}, headers=KEY).json()["token"]
    # session token 能呼叫 chat,但不能再換 token
    r = client.post("/v1/chat/completions", json={"stream": False}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200 and r.json()["spike"]["auth"] == "session"
    assert client.post("/bridge/session", json={"user": "b@example.com"},
                       headers={"Authorization": f"Bearer {tok}"}).status_code == 403


def test_tampered_token_rejected():
    tok = client.post("/bridge/session", json={"user": "a@example.com"}, headers=KEY).json()["token"]
    u, exp, sig = tok.split(".")
    forged = f"{u}.{int(exp) + 9999}.{sig}"
    assert client.post("/v1/chat/completions", json={}, headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_non_stream_delay():
    r = client.post("/v1/chat/completions", json={"spike": {"delay_ms": 300}}, headers=KEY)
    body = r.json()
    assert body["choices"][0]["message"]["content"] == "echo"
    assert body["spike"]["slept_ms"] >= 290


def test_stream_emits_openai_chunks_and_done():
    with client.stream("POST", "/v1/chat/completions",
                       json={"stream": True, "spike": {"tokens": 3, "interval_ms": 0}}, headers=KEY) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        lines = [ln for ln in r.iter_lines() if ln.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"
    chunks = [json.loads(ln[6:]) for ln in lines[:-1]]
    text = "".join(c["choices"][0]["delta"].get("content", "") for c in chunks)
    assert text == "字1 字2 字3 "
    assert chunks[-1]["choices"][0]["finish_reason"] == "stop"


def test_cors_preflight_allows_authorization_header():
    r = client.options("/v1/chat/completions", headers={
        "Origin": "https://example.apps.test", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] in ("*", "https://example.apps.test")
