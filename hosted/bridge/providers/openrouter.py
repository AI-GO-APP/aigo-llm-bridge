"""openrouter/* :原樣轉送到 OpenRouter 的 chat/completions(只把 model 換成去掉前綴的名稱)。"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from ..errors import BridgeError, provider_error
from .base import CallContext

NAME = "OpenRouter"
BASE = "https://openrouter.ai/api/v1"


class OpenRouterProvider:
    name = "openrouter"

    def __init__(self, api_key: str, *, client: httpx.AsyncClient | None = None, base_url: str = BASE):
        if not api_key and client is None:
            raise BridgeError(503, "provider_not_configured", "Bridge 沒有設定 OPENROUTER_API_KEY")
        self.base = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # 長回應可能超過一分鐘;連線逾時短、讀取逾時長
        self.client = client or httpx.AsyncClient(timeout=httpx.Timeout(280.0, connect=10.0))

    def _body(self, req: dict, model: str, stream: bool) -> dict:
        body = {**req, "model": model, "stream": stream}
        if "models" in body and isinstance(body["models"], list):
            body["models"] = [m.removeprefix("openrouter/") for m in body["models"]]
        return body

    @staticmethod
    def _error(resp: httpx.Response) -> BridgeError:
        message = ""
        try:
            err = resp.json().get("error") or {}
            message = err.get("message") if isinstance(err, dict) else str(err)
        except (ValueError, AttributeError):
            pass
        return provider_error(NAME, resp.status_code, message or "", resp.headers.get("retry-after"))

    async def complete(self, req: dict, model: str, ctx: CallContext) -> dict:
        try:
            resp = await self.client.post(f"{self.base}/chat/completions", headers=self.headers,
                                          json=self._body(req, model, False))
        except httpx.HTTPError:
            raise provider_error(NAME, None) from None
        if resp.status_code >= 400:
            raise self._error(resp)
        data = resp.json()
        if isinstance(data.get("error"), dict):   # OpenRouter 有時以 200 帶錯誤
            raise provider_error(NAME, int(data["error"].get("code") or 502), data["error"].get("message") or "")
        ctx.served_by = str(data.get("model") or model)
        ctx.usage = data.get("usage") or {}
        data["model"] = ctx.model_label
        return data

    async def stream(self, req: dict, model: str, ctx: CallContext) -> AsyncIterator[dict]:
        body = self._body(req, model, True)
        try:
            async with self.client.stream("POST", f"{self.base}/chat/completions", headers=self.headers,
                                          json=body) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    raise self._error(resp)
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue   # 忽略 OpenRouter 的保活註解行
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("usage"):
                        ctx.usage = chunk["usage"]
                    if chunk.get("model"):
                        ctx.served_by = str(chunk["model"])
                        chunk["model"] = ctx.model_label
                    yield chunk
        except httpx.HTTPError:
            yield {"error": provider_error(NAME, None).body()["error"]}
