import asyncio
import json

import anthropic
import httpx
import httpx2
import pytest

from bridge.errors import BridgeError
from bridge.providers.anthropic import AnthropicProvider
from bridge.providers.base import CallContext
from bridge.providers.openrouter import OpenRouterProvider


def run(coro):
    return asyncio.run(coro)


async def collect(agen):
    return [x async for x in agen]


class _Events:
    def __init__(self, events, fail_after=None):
        self.events, self.fail_after = events, fail_after

    def __aiter__(self):
        return self._gen()

    async def _gen(self):
        for i, ev in enumerate(self.events):
            if self.fail_after is not None and i == self.fail_after:
                raise anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com"))
            yield ev


class FakeMessages:
    def __init__(self, calls, reply=None, error=None, events=None, fail_after=None):
        self.calls, self.reply, self.error, self.events, self.fail_after = calls, reply, error, events, fail_after

    async def create(self, **kw):
        self.calls.append(kw)
        if self.error:
            raise self.error
        if kw.get("stream"):
            return _Events(self.events or [], self.fail_after)
        return self.reply


class FakeClient:
    def __init__(self, **kw):
        self.calls = []
        self.messages = FakeMessages(self.calls, **kw)
        self.beta = type("B", (), {"messages": self.messages})()


REPLY = {"id": "msg_1", "model": "claude-opus-5", "stop_reason": "end_turn",
         "content": [{"type": "text", "text": "嗨"}], "usage": {"input_tokens": 3, "output_tokens": 1}}
REQ = {"messages": [{"role": "user", "content": "hi"}], "temperature": 0.5}


def test_anthropic_complete_uses_beta_fallbacks_and_drops_sampling():
    fake = FakeClient(reply=REPLY)
    ctx = CallContext(source="S", user="u", model_label="anthropic/claude-opus-5")
    out = run(AnthropicProvider("", client=fake).complete(REQ, "claude-opus-5", ctx))
    call = fake.calls[0]
    assert call["betas"] == ["server-side-fallback-2026-07-01"]
    assert call["extra_body"] == {"fallbacks": "default"}
    assert "temperature" not in call
    assert ctx.dropped == ["temperature"]
    assert out["choices"][0]["message"]["content"] == "嗨"
    assert ctx.served_by == "claude-opus-5" and ctx.usage["total_tokens"] == 4


def test_anthropic_plain_call_for_models_without_fallbacks():
    fake = FakeClient(reply=REPLY)
    run(AnthropicProvider("", client=fake).complete(REQ, "claude-haiku-4-5",
                                                    CallContext("S", "u", "anthropic/claude-haiku-4-5")))
    assert "betas" not in fake.calls[0] and fake.calls[0]["temperature"] == 0.5


def _status_error(cls, status, body, headers=None):
    resp = httpx2.Response(status, request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages"),
                           json=body, headers=headers or {})
    return cls("x", response=resp, body=body)


@pytest.mark.parametrize("exc,status,code", [
    (lambda: _status_error(anthropic.RateLimitError, 429, {"error": {"message": "slow"}}, {"retry-after": "7"}),
     429, "provider_rate_limited"),
    (lambda: _status_error(anthropic.AuthenticationError, 401, {"error": {"message": "bad key sk-ant-xxx"}}),
     502, "provider_auth"),
    (lambda: _status_error(anthropic.BadRequestError, 400, {"error": {"message": "roles must alternate"}}),
     400, "provider_bad_request"),
    (lambda: anthropic.APIConnectionError(request=httpx2.Request("POST", "https://api.anthropic.com")),
     502, "provider_unreachable"),
])
def test_anthropic_errors_are_mapped(exc, status, code):
    fake = FakeClient(error=exc())
    with pytest.raises(BridgeError) as e:
        run(AnthropicProvider("", client=fake).complete(REQ, "claude-haiku-4-5", CallContext("S", "u", "m")))
    assert (e.value.status, e.value.code) == (status, code)
    assert "sk-ant" not in e.value.message        # 401 的上游訊息不回傳
    if code == "provider_rate_limited":
        assert e.value.headers == {"Retry-After": "7"}
    if code == "provider_bad_request":
        assert "roles must alternate" in e.value.message


EVENTS = [
    {"type": "message_start", "message": {"model": "claude-opus-5", "usage": {"input_tokens": 5}}},
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "OK"}},
    {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 1}},
    {"type": "message_stop"},
]


def test_anthropic_stream_and_usage_opt_in():
    ctx = CallContext("S", "u", "anthropic/claude-opus-5")
    chunks = run(collect(AnthropicProvider("", client=FakeClient(events=EVENTS)).stream(
        {**REQ, "stream_options": {"include_usage": True}}, "claude-opus-5", ctx)))
    assert "".join(c["choices"][0]["delta"].get("content", "") for c in chunks) == "OK"
    assert chunks[-1]["usage"]["completion_tokens"] == 1
    assert ctx.usage["prompt_tokens"] == 5
    chunks = run(collect(AnthropicProvider("", client=FakeClient(events=EVENTS)).stream(
        REQ, "claude-opus-5", CallContext("S", "u", "m"))))
    assert "usage" not in chunks[-1]


def test_anthropic_stream_error_midway_becomes_error_event():
    chunks = run(collect(AnthropicProvider("", client=FakeClient(events=EVENTS, fail_after=3)).stream(
        REQ, "claude-opus-5", CallContext("S", "u", "m"))))
    assert chunks[-1] == {"error": {"code": "provider_unreachable", "message": "Anthropic 暫時連不上",
                                    "provider_status": None}}


def _openrouter(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenRouterProvider("or-key", client=client, base_url="https://or.test/api/v1")


def test_openrouter_passthrough_keeps_extra_fields_and_strips_prefix():
    seen = {}

    def handler(request):
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"id": "gen-1", "model": "anthropic/claude-haiku-4.5",
                                         "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"},
                                                      "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 1, "completion_tokens": 1}})

    ctx = CallContext("S", "u", "openrouter/anthropic/claude-haiku-4.5")
    req = {**REQ, "models": ["openrouter/anthropic/claude-haiku-4.5", "openai/gpt-5.4-mini"],
           "provider": {"data_collection": "deny"}}
    out = run(_openrouter(handler).complete(req, "anthropic/claude-haiku-4.5", ctx))
    assert seen["body"]["model"] == "anthropic/claude-haiku-4.5"
    assert seen["body"]["models"] == ["anthropic/claude-haiku-4.5", "openai/gpt-5.4-mini"]
    assert seen["body"]["provider"] == {"data_collection": "deny"} and seen["body"]["temperature"] == 0.5
    assert seen["auth"] == "Bearer or-key"
    assert out["model"] == "openrouter/anthropic/claude-haiku-4.5"
    assert ctx.served_by == "anthropic/claude-haiku-4.5"


def test_openrouter_error_in_200_body_and_status_mapping():
    def handler(request):
        return httpx.Response(200, json={"error": {"code": 429, "message": "busy"}})

    with pytest.raises(BridgeError) as e:
        run(_openrouter(handler).complete(REQ, "x/y", CallContext("S", "u", "m")))
    assert e.value.code == "provider_rate_limited"

    with pytest.raises(BridgeError) as e:
        run(_openrouter(lambda r: httpx.Response(401, json={"error": {"message": "no"}})).complete(
            REQ, "x/y", CallContext("S", "u", "m")))
    assert e.value.code == "provider_auth"


def test_openrouter_stream_skips_keepalive_and_stops_at_done():
    sse = (": OPENROUTER PROCESSING\n\n"
           'data: {"id":"g","model":"a/b","choices":[{"index":0,"delta":{"content":"he"}}]}\n\n'
           'data: {"id":"g","model":"a/b","choices":[{"index":0,"delta":{"content":"y"},"finish_reason":"stop"}],'
           '"usage":{"prompt_tokens":2,"completion_tokens":2}}\n\n'
           "data: [DONE]\n\n")

    def handler(request):
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})

    ctx = CallContext("S", "u", "openrouter/a/b")
    chunks = run(collect(_openrouter(handler).stream(REQ, "a/b", ctx)))
    assert "".join(c["choices"][0]["delta"].get("content", "") for c in chunks) == "hey"
    assert all(c["model"] == "openrouter/a/b" for c in chunks)
    assert ctx.usage == {"prompt_tokens": 2, "completion_tokens": 2}
