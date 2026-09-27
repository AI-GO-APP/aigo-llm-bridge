"""anthropic/* :以官方 Python SDK(AsyncAnthropic)呼叫 Messages API。"""

from __future__ import annotations

from typing import AsyncIterator

import anthropic

from ..anthropic_map import StreamTranslator, from_anthropic_message, to_anthropic, usage_to_openai
from ..errors import BridgeError, provider_error
from .base import CallContext

NAME = "Anthropic"


def _as_dict(obj) -> dict:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json", exclude_none=False)
    return dict(obj)


def _map_error(exc: Exception) -> BridgeError:
    if isinstance(exc, anthropic.APIStatusError):
        message = ""
        try:
            body = exc.response.json()
            message = (body.get("error") or {}).get("message") or ""
        except Exception:  # noqa: BLE001
            pass
        return provider_error(NAME, exc.status_code, message, exc.response.headers.get("retry-after"))
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return provider_error(NAME, None)
    raise exc


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, *, fallbacks: bool = True, client=None):
        if not api_key and client is None:
            raise BridgeError(503, "provider_not_configured", "Bridge 沒有設定 ANTHROPIC_API_KEY")
        self.fallbacks = fallbacks
        # SDK 自己會對 429 / 5xx / 連線錯誤重試兩次
        self.client = client or anthropic.AsyncAnthropic(api_key=api_key, max_retries=2)

    def _call(self, prep, **extra):
        if prep.betas:
            return self.client.beta.messages.create(**prep.kwargs, betas=prep.betas,
                                                     extra_body=prep.extra_body, **extra)
        return self.client.messages.create(**prep.kwargs, **extra)

    async def complete(self, req: dict, model: str, ctx: CallContext) -> dict:
        prep = to_anthropic(req, model, stream=False, fallbacks=self.fallbacks)
        ctx.dropped = prep.dropped
        try:
            msg = _as_dict(await self._call(prep))
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            raise _map_error(exc) from None
        out = from_anthropic_message(msg, ctx.model_label)
        ctx.served_by = msg.get("model") or model
        ctx.usage = out["usage"]
        return out

    async def stream(self, req: dict, model: str, ctx: CallContext) -> AsyncIterator[dict]:
        prep = to_anthropic(req, model, stream=True, fallbacks=self.fallbacks)
        ctx.dropped = prep.dropped
        include_usage = bool((req.get("stream_options") or {}).get("include_usage"))
        tr = StreamTranslator(ctx.model_label, include_usage=True)
        try:
            events = await self._call(prep, stream=True)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            raise _map_error(exc) from None   # 還沒開始送:讓路由回一般錯誤回應
        try:
            async for event in events:
                ev = _as_dict(event)
                if ev.get("type") == "message_start":
                    ctx.served_by = (ev.get("message") or {}).get("model") or model
                for chunk in tr.feed(ev):
                    if not include_usage:
                        chunk.pop("usage", None)
                    yield chunk
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            err = _map_error(exc)
            yield {"error": err.body()["error"]}
        finally:
            ctx.usage = usage_to_openai(tr.usage)
