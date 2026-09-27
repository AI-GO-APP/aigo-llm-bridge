import asyncio
import json

import httpx
import pytest

from bridge.auth import sign_request
from bridge.config import Settings
from bridge.errors import BridgeError
from bridge.app import create_app
from bridge.store import MemoryStore

KEY = "source-key-1"
AUTH = {"Authorization": f"Bearer {KEY}"}


class FakeProvider:
    def __init__(self, name="anthropic", error=None, stream_error_first=None):
        self.name, self.error, self.stream_error_first = name, error, stream_error_first
        self.calls = []

    async def complete(self, req, model, ctx):
        self.calls.append(model)
        if self.error:
            raise self.error
        ctx.dropped = ["temperature"] if "temperature" in req else []
        ctx.served_by = model
        ctx.usage = {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}
        return {"id": "x", "object": "chat.completion", "model": ctx.model_label,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": f"echo:{model}"},
                             "finish_reason": "stop"}], "usage": ctx.usage}

    async def stream(self, req, model, ctx):
        self.calls.append(model)
        if self.stream_error_first:
            raise self.stream_error_first
        for piece in ("a", "b"):
            yield {"id": "x", "object": "chat.completion.chunk", "model": ctx.model_label,
                   "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}]}


def make(**overrides):
    base = {"anthropic_api_key": "k", "openrouter_api_key": "k", "store_backend": "memory",
            "sync_timeout_s": 3.0, "claim_wait_s": 1.0}
    settings = Settings(source_keys={"APP": KEY}, session_secret="s" * 32, **{**base, **overrides})
    providers = {"anthropic": FakeProvider("anthropic"), "openrouter": FakeProvider("openrouter")}
    app = create_app(settings, MemoryStore(), providers)
    return app, providers


def client(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://bridge.test")


def run(coro):
    return asyncio.run(coro)


MSG = {"messages": [{"role": "user", "content": "hi"}]}


# ── 驗證 ──────────────────────────────────────────────────────────────────
def test_auth_variants():
    app, _ = make()

    async def go():
        async with client(app) as c:
            assert (await c.post("/v1/chat/completions", json=MSG)).status_code == 401
            assert (await c.post("/v1/chat/completions", json=MSG,
                                 headers={"Authorization": "Bearer nope"})).status_code == 401
            body = json.dumps({**MSG, "model": "anthropic/claude-opus-5"}).encode()
            ok = await c.post("/v1/chat/completions", content=body,
                              headers={**sign_request(KEY, "APP", body), "Content-Type": "application/json"})
            assert ok.status_code == 200
            tampered = sign_request(KEY, "APP", body)
            bad = await c.post("/v1/chat/completions", content=body + b" ", headers=tampered)
            assert bad.status_code == 401
            tok = (await c.post("/bridge/session", json={"user": "u1"}, headers=AUTH)).json()["token"]
            s_ok = await c.post("/v1/chat/completions", json={**MSG, "model": "anthropic/claude-opus-5"},
                                headers={"Authorization": f"Bearer {tok}"})
            assert s_ok.status_code == 200
            again = await c.post("/bridge/session", json={"user": "u2"}, headers={"Authorization": f"Bearer {tok}"})
            assert again.status_code == 403
    run(go())


# ── 路由與相容性 ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("model,provider,upstream", [
    ("anthropic/claude-opus-5", "anthropic", "claude-opus-5"),
    ("anthropic/claude-haiku-4.5", "anthropic", "claude-haiku-4-5"),     # OpenRouter 的點號寫法
    ("claude-sonnet-5", "anthropic", "claude-sonnet-5"),
    ("openrouter/anthropic/claude-haiku-4.5", "openrouter", "anthropic/claude-haiku-4.5"),
    ("openai/gpt-5.4-mini", "openrouter", "openai/gpt-5.4-mini"),       # 其他廠牌交給 OpenRouter
])
def test_routing_keeps_openrouter_style_callers_working(model, provider, upstream):
    app, providers = make()

    async def go():
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": model, "temperature": 0.3}, headers=AUTH)
            assert r.status_code == 200
            assert providers[provider].calls == [upstream]
            assert r.json()["model"] == model
            assert r.headers["x-bridge-dropped"] == "temperature"
            # egress 的 ctx.http.call 拿不到標頭,所以本體也要有(E2E 實測)
            assert r.json()["x_bridge"]["dropped"] == ["temperature"]
            assert r.json()["x_bridge"]["served_by"] == r.headers.get("x-bridge-served-by")
    run(go())


def test_unknown_model_and_bad_body():
    app, _ = make()

    async def go():
        async with client(app) as c:
            assert (await c.post("/v1/chat/completions", json={**MSG, "model": "gpt-4"},
                                 headers=AUTH)).json()["error"]["code"] == "unknown_provider"
            assert (await c.post("/v1/chat/completions", content=b"{", headers=AUTH)).json()["error"]["code"] == "bad_json"
            assert (await c.post("/v1/chat/completions", json={"model": "x"},
                                 headers=AUTH)).json()["error"]["code"] == "bad_request"
    run(go())


# ── 串流 ──────────────────────────────────────────────────────────────────
def test_stream_ok_and_error_before_first_chunk_is_plain_http_error():
    app, providers = make()

    async def go():
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "anthropic/claude-opus-5", "stream": True},
                             headers=AUTH)
            lines = [ln for ln in r.text.split("\n") if ln.startswith("data: ")]
            assert r.headers["content-type"].startswith("text/event-stream")
            assert lines[-1] == "data: [DONE]"
            assert "".join(json.loads(ln[6:])["choices"][0]["delta"]["content"] for ln in lines[:-1]) == "ab"

            providers["anthropic"].stream_error_first = BridgeError(429, "provider_rate_limited", "busy",
                                                                    headers={"Retry-After": "3"})
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "anthropic/claude-opus-5", "stream": True},
                             headers=AUTH)
            assert r.status_code == 429 and r.headers["retry-after"] == "3"
            assert r.json()["error"]["code"] == "provider_rate_limited"
    run(go())


# ── 非同步與 responses ────────────────────────────────────────────────────
def test_async_job_and_responses_endpoint():
    app, _ = make()

    async def go():
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "anthropic/claude-opus-5"},
                             headers={**AUTH, "X-Bridge-Async": "true", "X-Bridge-User": "u1"})
            assert r.status_code == 202
            job_id = r.json()["id"]
            for _ in range(50):
                status = (await c.get(f"/v1/jobs/{job_id}", headers={**AUTH, "X-Bridge-User": "u1"})).json()
                if status["status"] == "done":
                    break
                await asyncio.sleep(0.02)
            assert status["result"]["choices"][0]["message"]["content"] == "echo:claude-opus-5"
            other = await c.get(f"/v1/jobs/{job_id}", headers={**AUTH, "X-Bridge-User": "someone-else"})
            assert other.status_code == 404

            r = await c.post("/v1/responses", headers=AUTH, json={
                "model": "anthropic/claude-opus-5", "instructions": "be brief", "input": "hi", "max_output_tokens": 50})
            body = r.json()
            assert body["output_text"] == "echo:claude-opus-5"
            assert body["usage"] == {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3}
    run(go())


# ── local:綁定、只領本人工單、串流、逾時、撤銷 ──────────────────────────
async def enroll(c, user):
    code = (await c.post("/bridge/enrollments", headers={**AUTH, "X-Bridge-User": user})).json()["code"]
    r = await c.post("/worker/enroll", json={"code": code, "name": f"{user}-pc", "os": "test", "version": "0"})
    return {"Authorization": f"Bearer {r.json()['device_key']}"}


def test_local_requires_own_worker_and_never_reroutes():
    app, _ = make()

    async def go():
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "local/self"},
                             headers={**AUTH, "X-Bridge-User": "alice"})
            assert r.status_code == 409 and r.json()["error"]["code"] == "no_worker_for_user"
            await enroll(c, "bob")    # 有別人的 worker 也不算
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "local/self"},
                             headers={**AUTH, "X-Bridge-User": "alice"})
            assert r.status_code == 409
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "local/bob"},
                             headers={**AUTH, "X-Bridge-User": "alice"})
            assert r.json()["error"]["code"] == "unsupported_local_target"
    run(go())


def test_local_stream_end_to_end_and_other_owner_cannot_claim():
    app, _ = make()

    async def go():
        async with client(app) as c:
            alice = await enroll(c, "alice")
            bob = await enroll(c, "bob")

            async def caller():
                r = await c.post("/v1/chat/completions", headers={**AUTH, "X-Bridge-User": "alice"},
                                 json={"model": "local/self:haiku", "stream": True,
                                       "stream_options": {"include_usage": True},
                                       "messages": [{"role": "system", "content": "sys"},
                                                    {"role": "user", "content": "q1"},
                                                    {"role": "assistant", "content": "a1"},
                                                    {"role": "user", "content": "q2"}]})
                return r

            async def workers():
                assert (await c.post("/worker/claim", headers=bob)).json()["job"] is None   # bob 領不到 alice 的
                job = None
                for _ in range(20):
                    job = (await c.post("/worker/claim", headers=alice)).json()["job"]
                    if job:
                        break
                assert job["model"] == "haiku" and job["system"] == "sys"
                assert job["effort"] is None and job["thinking"] is None   # 沒指定就照模型原本的行為
                assert "q1" in job["prompt"] and job["prompt"].rstrip().endswith("q2")
                jid = job["job_id"]
                assert (await c.post(f"/worker/jobs/{jid}/chunk", headers=bob, json={"text": "x"})).status_code == 404
                await c.post(f"/worker/jobs/{jid}/chunk", headers=alice, json={"text": "你"})
                await c.post(f"/worker/jobs/{jid}/chunk", headers=alice, json={"text": "你好"})
                await c.post(f"/worker/jobs/{jid}/result", headers=alice,
                             json={"text": "你好!", "usage": {"input_tokens": 9, "output_tokens": 3},
                                   "cost_usd": 0.001, "model": "claude-haiku-4-5", "duration_ms": 1200})

            r, _ = await asyncio.gather(caller(), workers())
            lines = [ln for ln in r.text.split("\n") if ln.startswith("data: ") and ln != "data: [DONE]"]
            chunks = [json.loads(ln[6:]) for ln in lines]
            text = "".join(ch["choices"][0]["delta"].get("content", "") for ch in chunks)
            assert text == "你好!"
            assert chunks[-1]["usage"]["prompt_tokens"] == 9
            # 標頭送出時還不知道實際型號 → 放在最後一個 chunk(E2E 畫面上「實際型號」原本是空的)
            assert chunks[-1]["model"] == "claude-haiku-4-5"
            assert chunks[-1]["x_bridge"] == {"served_by": "local:claude-haiku-4-5", "dropped": []}
            usage_rows = app.state.store.tables["usage"]
            assert any(u["provider"] == "local" and u["owner"] == "alice" for u in usage_rows)
            job = app.state.store.tables["jobs"][0]
            assert job["status"] == "done" and job["request_json"] is None   # 提示在完成後清除
    run(go())


def test_local_sync_timeout_returns_202_then_result_via_jobs():
    app, _ = make()
    app.state.local.s = app.state.settings.__class__(**{**app.state.settings.__dict__, "sync_timeout_s": 0.3})

    async def go():
        async with client(app) as c:
            alice = await enroll(c, "alice")
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "local/self"},
                             headers={**AUTH, "X-Bridge-User": "alice"})
            assert r.status_code == 202
            job_id = r.json()["id"]
            job = (await c.post("/worker/claim", headers=alice)).json()["job"]
            assert job["job_id"] == job_id
            await c.post(f"/worker/jobs/{job_id}/result", headers=alice,
                         json={"text": "late", "usage": {"input_tokens": 1, "output_tokens": 1}})
            res = (await c.get(f"/v1/jobs/{job_id}", headers={**AUTH, "X-Bridge-User": "alice"})).json()
            assert res["status"] == "done" and res["result"]["choices"][0]["message"]["content"] == "late"
    run(go())


def test_revoked_worker_is_locked_out_and_listed():
    app, _ = make()

    async def go():
        async with client(app) as c:
            alice = await enroll(c, "alice")
            listed = (await c.get("/bridge/workers", headers={**AUTH, "X-Bridge-User": "alice"})).json()["workers"]
            assert len(listed) == 1 and listed[0]["online"] is True
            wid = listed[0]["id"]
            assert (await c.post(f"/bridge/workers/{wid}/revoke",
                                 headers={**AUTH, "X-Bridge-User": "bob"})).status_code == 404
            assert (await c.post(f"/bridge/workers/{wid}/revoke",
                                 headers={**AUTH, "X-Bridge-User": "alice"})).status_code == 200
            assert (await c.post("/worker/claim", headers=alice)).status_code == 401
    run(go())


def test_enrollment_code_single_use_and_not_from_browser_token():
    app, _ = make()

    async def go():
        async with client(app) as c:
            code = (await c.post("/bridge/enrollments", headers={**AUTH, "X-Bridge-User": "alice"})).json()["code"]
            assert (await c.post("/worker/enroll", json={"code": code})).status_code == 200
            assert (await c.post("/worker/enroll", json={"code": code})).json()["error"]["code"] == "bad_enrollment_code"
            tok = (await c.post("/bridge/session", json={"user": "alice"}, headers=AUTH)).json()["token"]
            assert (await c.post("/bridge/enrollments", headers={"Authorization": f"Bearer {tok}"})).status_code == 403
    run(go())


def test_local_rejects_tools_and_images():
    app, _ = make()

    async def go():
        async with client(app) as c:
            await enroll(c, "alice")
            r = await c.post("/v1/chat/completions", headers={**AUTH, "X-Bridge-User": "alice"}, json={
                **MSG, "model": "local/self", "tools": [{"type": "function", "function": {"name": "f"}}]})
            assert r.json()["error"]["code"] == "local_no_tools"
            r = await c.post("/v1/chat/completions", headers={**AUTH, "X-Bridge-User": "alice"}, json={
                "model": "local/self", "messages": [{"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": "https://x/a.png"}}]}]})
            assert r.json()["error"]["code"] == "local_no_images"
    run(go())


def test_no_worker_hint_only_points_to_configured_backends():
    """沒設雲端金鑰時,409 不可以叫人改用一個會回 503 的後端(E2E 畫面上實際看到的死路)。"""
    async def message(**keys):
        app, _ = make(**keys)
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "local/self"},
                             headers={**AUTH, "X-Bridge-User": "alice"})
        assert r.status_code == 409
        return r.json()["error"]["message"]

    assert "anthropic/*" in asyncio.run(message())
    bare = asyncio.run(message(anthropic_api_key="", openrouter_api_key=""))
    assert "anthropic" not in bare and "OpenRouter" not in bare
    assert "OpenRouter" in asyncio.run(message(anthropic_api_key=""))
