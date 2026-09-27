"""model: "auto" —— 使用者自己選優先,另一個當備援(bridge/routing.py、docs/05 §3)。"""

import asyncio
import json

from bridge.errors import BridgeError, provider_error
from test_app import AUTH, MSG, client, enroll, make, run

CLOUD = "openrouter/vendor/model-x"
ALICE = {**AUTH, "X-Bridge-User": "alice"}


def auto_app(**overrides):
    return make(auto_cloud_model=CLOUD, **overrides)


async def set_priority(c, priority, headers=ALICE):
    r = await c.put("/bridge/preferences", json={"priority": priority}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_auto_refuses_until_the_user_has_chosen():
    app, providers = auto_app()

    async def go():
        async with client(app) as c:
            view = (await c.get("/bridge/preferences", headers=ALICE)).json()
            assert view["priority"] is None
            assert [ch["id"] for ch in view["choices"]] == ["local", "cloud"]
            assert view["choices"][1] == {"id": "cloud", "label": "雲端(OpenRouter)", "model": CLOUD,
                                          "available": True}
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 409 and r.json()["error"]["code"] == "priority_required"
            assert providers["openrouter"].calls == []          # 沒選之前不偷偷套預設
            bad = await c.put("/bridge/preferences", json={"priority": "fastest"}, headers=ALICE)
            assert bad.status_code == 400 and bad.json()["error"]["code"] == "bad_priority"
    run(go())


def test_cloud_first_uses_cloud_and_reports_priority():
    app, providers = auto_app()

    async def go():
        async with client(app) as c:
            await set_priority(c, "cloud")
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 200
            assert providers["openrouter"].calls == ["vendor/model-x"]
            assert r.json()["x_bridge"]["priority"] == "cloud" and r.json()["x_bridge"]["fallback"] is None
            assert r.headers["x-bridge-priority"] == "cloud" and "x-bridge-fallback" not in r.headers
    run(go())


def test_local_first_without_worker_falls_back_to_cloud():
    app, providers = auto_app()

    async def go():
        async with client(app) as c:
            await set_priority(c, "local")
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 200 and providers["openrouter"].calls == ["vendor/model-x"]
            meta = r.json()["x_bridge"]
            assert meta["fallback"] == {"from": "local/self", "reason": "no_worker_for_user"}
            assert r.headers["x-bridge-fallback"] == "local/self:no_worker_for_user"
            statuses = [u["status"] for u in app.state.store.tables["usage"]]
            assert statuses == ["fallback", "ok"]               # 先試的那次也記帳,看得出備援用了幾次
            assert app.state.store.tables["jobs"] == []           # 沒有 worker 時根本沒開工單
    run(go())


def test_cloud_first_failure_falls_back_to_own_worker():
    app, providers = auto_app()
    providers["openrouter"].error = provider_error("OpenRouter", 503)

    async def go():
        async with client(app) as c:
            alice = await enroll(c, "alice")
            await set_priority(c, "cloud")

            async def worker():
                for _ in range(40):
                    job = (await c.post("/worker/claim", headers=alice)).json()["job"]
                    if job:
                        await c.post(f"/worker/jobs/{job['job_id']}/result", headers=alice,
                                     json={"text": "本機回答", "model": "claude-sonnet-5"})
                        return
                    await asyncio.sleep(0.05)

            r, _ = await asyncio.gather(
                c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE), worker())
            assert r.status_code == 200
            assert r.json()["choices"][0]["message"]["content"] == "本機回答"
            assert r.json()["x_bridge"]["fallback"] == {"from": CLOUD, "reason": "provider_error"}
            assert r.json()["x_bridge"]["served_by"] == "local:claude-sonnet-5"
            assert "fallback" in [u["status"] for u in app.state.store.tables["usage"]]
    run(go())


def test_request_errors_do_not_fall_back():
    app, providers = auto_app()
    providers["openrouter"].error = BridgeError(400, "provider_bad_request", "bad field")

    async def go():
        async with client(app) as c:
            await enroll(c, "alice")
            await set_priority(c, "cloud")
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 400 and r.json()["error"]["code"] == "provider_bad_request"
            assert app.state.store.tables["jobs"] == []        # 沒有改派給本機
    run(go())


def test_both_failing_reports_both():
    app, providers = auto_app()
    providers["openrouter"].error = provider_error("OpenRouter", 429, retry_after="7")

    async def go():
        async with client(app) as c:
            await set_priority(c, "local")
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 429 and r.json()["error"]["code"] == "provider_rate_limited"
            assert "local/self:no_worker_for_user" in r.json()["error"]["message"]
            assert r.headers["x-bridge-fallback"] == "local/self:no_worker_for_user"
            assert r.headers["retry-after"] == "7"
    run(go())


def test_stream_falls_back_before_any_output():
    app, providers = auto_app()

    async def go():
        async with client(app) as c:
            alice = await enroll(c, "alice")
            await set_priority(c, "local")

            async def worker_fails():
                for _ in range(40):
                    job = (await c.post("/worker/claim", headers=alice)).json()["job"]
                    if job:
                        await c.post(f"/worker/jobs/{job['job_id']}/fail", headers=alice,
                                     json={"code": "claude_exit", "message": "boom"})
                        return
                    await asyncio.sleep(0.05)

            r, _ = await asyncio.gather(
                c.post("/v1/chat/completions", json={**MSG, "model": "auto", "stream": True}, headers=ALICE),
                worker_fails())
            assert r.status_code == 200
            assert r.headers["x-bridge-fallback"] == "local/self:claude_exit"
            chunks = [json.loads(ln[6:]) for ln in r.text.split("\n") if ln.startswith("data: {")]
            text = "".join(ch["choices"][0]["delta"].get("content", "") for ch in chunks if "choices" in ch)
            assert text == "ab" and not any("error" in ch for ch in chunks)
            assert providers["openrouter"].calls == ["vendor/model-x"]
    run(go())


def test_models_override_and_validation():
    app, providers = auto_app()

    async def go():
        async with client(app) as c:
            await set_priority(c, "cloud")
            r = await c.post("/v1/chat/completions", headers=ALICE, json={
                **MSG, "model": "auto", "models": ["local/self:haiku", "openrouter/other/model-y"]})
            assert r.status_code == 200 and providers["openrouter"].calls == ["other/model-y"]
            assert "models" not in (providers["openrouter"].last_req or {})
            r = await c.post("/v1/chat/completions", headers=ALICE, json={
                **MSG, "model": "auto", "models": ["local/self", "local/self:haiku"]})
            assert r.status_code == 400 and r.json()["error"]["code"] == "bad_auto_models"
            r = await c.post("/v1/chat/completions", headers=ALICE, json={
                **MSG, "model": "auto", "models": ["gpt-4o"]})
            assert r.status_code == 400 and r.json()["error"]["code"] == "bad_auto_models"
    run(go())


def test_no_cloud_candidate_means_local_only():
    app, providers = make()          # 沒設 BRIDGE_AUTO_CLOUD、請求也沒帶 models

    async def go():
        async with client(app) as c:
            view = await set_priority(c, "cloud")
            assert view["choices"][1]["available"] is False
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=ALICE)
            assert r.status_code == 409 and r.json()["error"]["code"] == "no_worker_for_user"
            assert providers["openrouter"].calls == []
    run(go())


def test_preferences_per_app_and_per_user_and_from_browser_token():
    app, _ = auto_app(source_keys={"APP": "source-key-1", "OTHER": "source-key-2"})

    async def go():
        async with client(app) as c:
            tok = (await c.post("/bridge/session", json={"user": "alice"}, headers=AUTH)).json()["token"]
            await set_priority(c, "local", headers={"Authorization": f"Bearer {tok}"})
            assert (await c.get("/bridge/preferences", headers=ALICE)).json()["priority"] == "local"
            bob = (await c.get("/bridge/preferences", headers={**AUTH, "X-Bridge-User": "bob"})).json()
            other = (await c.get("/bridge/preferences", headers={"Authorization": "Bearer source-key-2",
                                                                  "X-Bridge-User": "alice"})).json()
            assert bob["priority"] is None and other["priority"] is None
            await set_priority(c, "cloud")
            assert len(app.state.store.tables["prefs"]) == 1      # 改選是更新,不是多一筆
    run(go())


def test_auto_needs_a_user():
    app, _ = auto_app()

    async def go():
        async with client(app) as c:
            r = await c.post("/v1/chat/completions", json={**MSG, "model": "auto"}, headers=AUTH)
            assert r.status_code == 400 and r.json()["error"]["code"] == "user_required"
            models = (await c.get("/v1/models", headers=AUTH)).json()["data"]
            assert models[0]["id"] == "auto"
    run(go())
