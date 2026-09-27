import asyncio
import json

import httpx
import pytest

import bridge.app as app_mod
from bridge.anthropic_map import to_anthropic
from bridge.app import create_app
from bridge.config import Settings
from bridge.errors import BridgeError
from bridge.local import parse_local_model, render_for_worker, strip_json_fences
from bridge.reasoning import normalize
from bridge.store import MemoryStore

KEY = "k"
AUTH = {"Authorization": f"Bearer {KEY}"}
MSG = [{"role": "user", "content": "hi"}]


# ── 參數統一 ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("req,expected", [
    ({}, {"effort": None, "thinking": None, "budget": None}),                              # 預設:不替呼叫端決定
    ({"reasoning_effort": "high"}, {"effort": "high", "thinking": None, "budget": None}),
    ({"reasoning_effort": "minimal"}, {"effort": "low", "thinking": None, "budget": None}),
    ({"reasoning_effort": "none"}, {"effort": None, "thinking": "off", "budget": None}),
    ({"reasoning": {"effort": "medium"}}, {"effort": "medium", "thinking": None, "budget": None}),
    ({"reasoning": {"enabled": False}}, {"effort": None, "thinking": "off", "budget": None}),
    ({"reasoning": {"max_tokens": 2048}}, {"effort": None, "thinking": "on", "budget": 2048}),
    ({"thinking": {"type": "disabled"}}, {"effort": None, "thinking": "off", "budget": None}),
    ({"thinking": {"type": "enabled", "budget_tokens": 3000}}, {"effort": None, "thinking": "on", "budget": 3000}),
])
def test_normalize(req, expected):
    assert normalize(req) == expected


def test_normalize_rejects_unknown_effort():
    with pytest.raises(BridgeError):
        normalize({"reasoning_effort": "ultra"})


# ── 依模型轉成 Anthropic 參數 ─────────────────────────────────────────────
def prep(model, **kw):
    return to_anthropic({"messages": MSG, **kw}, model, stream=False, fallbacks=False)


def test_defaults_send_nothing():
    kw = prep("claude-opus-5").kwargs
    assert "thinking" not in kw and "output_config" not in kw


def test_effort_supported_vs_not():
    assert prep("claude-sonnet-5", reasoning_effort="low").kwargs["output_config"] == {"effort": "low"}
    p = prep("claude-haiku-4-5", reasoning_effort="low")
    assert "output_config" not in p.kwargs and p.dropped == ["reasoning_effort"]


@pytest.mark.parametrize("model,effort,sent,dropped", [
    ("claude-sonnet-5", None, {"type": "disabled"}, []),
    ("claude-opus-5", "high", {"type": "disabled"}, []),
    ("claude-opus-5", "max", None, ["thinking_off"]),          # Opus 5 在 xhigh/max 時不能關
    ("claude-opus-5-5", None, None, ["thinking_off"]),         # Opus 5.5 關不掉
    ("claude-fable-5-1", None, None, ["thinking_off"]),
    ("claude-haiku-4-5", None, None, []),                      # 舊世代:不帶就是不思考
])
def test_thinking_off_per_model(model, effort, sent, dropped):
    p = prep(model, reasoning={"enabled": False, **({"effort": effort} if effort else {})})
    assert p.kwargs.get("thinking") == sent
    assert p.dropped == dropped


def test_thinking_on_budget_vs_adaptive():
    assert prep("claude-haiku-4-5", reasoning={"max_tokens": 2000}, max_tokens=8000).kwargs["thinking"] == \
        {"type": "enabled", "budget_tokens": 2000}
    assert prep("claude-haiku-4-5", reasoning={"enabled": True}, max_tokens=500).dropped == ["thinking_on"]
    assert prep("claude-opus-4-8", reasoning={"enabled": True}).kwargs["thinking"] == {"type": "adaptive"}


# ── local 的模型指定與 JSON 外框 ─────────────────────────────────────────
@pytest.mark.parametrize("model,spec", [("local/self", ""), ("local/self:haiku", "haiku"),
                                        ("local/self:claude-opus-5", "claude-opus-5")])
def test_local_model_spec(model, spec):
    assert parse_local_model(model) == spec


@pytest.mark.parametrize("model", ["local/self:gpt-4", "local/self:claude-", "local/alice"])
def test_local_model_spec_rejects(model):
    with pytest.raises(BridgeError):
        parse_local_model(model)


def test_render_passes_reasoning_through():
    job = render_for_worker({"messages": MSG, "reasoning": {"effort": "low", "enabled": False}}, "claude-sonnet-5")
    assert (job["model"], job["effort"], job["thinking"]) == ("claude-sonnet-5", "low", "off")


@pytest.mark.parametrize("raw,clean", [
    ('```json\n{"a": 1}\n```', '{"a": 1}'),
    ('```\n{"a": 1}\n```', '{"a": 1}'),
    ('{"a": 1}', '{"a": 1}'),
    ('答案是 ```json\n{}\n```', '答案是 ```json\n{}\n```'),   # 不是整段被包住就不動
])
def test_strip_json_fences(raw, clean):
    assert strip_json_fences(raw) == clean


# ── 等待上限與串流收尾 ────────────────────────────────────────────────────
class SlowProvider:
    def __init__(self, delay):
        self.delay = delay

    async def complete(self, req, model, ctx):
        await asyncio.sleep(self.delay)
        return {"id": "x", "object": "chat.completion", "model": ctx.model_label,
                "choices": [{"index": 0, "message": {"role": "assistant", "content": "slow"}, "finish_reason": "stop"}],
                "usage": {}}

    async def stream(self, req, model, ctx):
        yield {"choices": [{"index": 0, "delta": {"content": "a"}}]}
        await asyncio.sleep(self.delay)
        yield {"choices": [{"index": 0, "delta": {"content": "b"}}]}


def make(delay):
    s = Settings(source_keys={"APP": KEY}, session_secret="s" * 32, anthropic_api_key="k", store_backend="memory")
    return create_app(s, MemoryStore(), {"anthropic": SlowProvider(delay)})


def run(coro):
    return asyncio.run(coro)


def test_wait_header_hands_off_to_job_then_result_is_fetchable():
    app = make(1.5)   # X-Bridge-Wait 最小 1 秒

    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://b") as c:
            r = await c.post("/v1/chat/completions", headers={**AUTH, "X-Bridge-Wait": "1"},
                             json={"model": "anthropic/claude-opus-5", "messages": MSG})
            assert r.status_code == 202
            job = r.json()["id"]
            await asyncio.sleep(0.8)
            res = (await c.get(f"/v1/jobs/{job}", headers=AUTH)).json()
            assert res["status"] == "done" and res["result"]["choices"][0]["message"]["content"] == "slow"
            # 不帶標頭:用 Bridge 預設(280 秒),直接等到結果
            r = await c.post("/v1/chat/completions", headers=AUTH,
                             json={"model": "anthropic/claude-opus-5", "messages": MSG})
            assert r.status_code == 200
            assert (await c.post("/v1/chat/completions", headers={**AUTH, "X-Bridge-Wait": "abc"},
                                 json={"model": "anthropic/claude-opus-5", "messages": MSG})).status_code == 400
    run(go())


def test_stream_ends_itself_before_platform_cut(monkeypatch):
    monkeypatch.setattr(app_mod, "STREAM_CAP_S", 0.2)
    app = make(1.0)

    async def go():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://b") as c:
            r = await c.post("/v1/chat/completions", headers=AUTH,
                             json={"model": "anthropic/claude-opus-5", "messages": MSG, "stream": True})
            lines = [ln for ln in r.text.split("\n") if ln.startswith("data: ")]
            assert lines[-1] == "data: [DONE]"
            assert json.loads(lines[-2][6:])["error"]["code"] == "stream_timeout"
    run(go())
