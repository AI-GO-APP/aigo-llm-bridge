"""provider 的共同介面。

每個 provider 收 OpenAI 形狀的請求,回 OpenAI 形狀的結果:
  complete(req, model, ctx) -> dict(chat.completion)
  stream(req, model, ctx)   -> 非同步產生 chat.completion.chunk(dict)
過程中把「丟掉了哪些參數」「實際由哪個模型回答」「usage」記進 ctx,給路由寫標頭與用量帳。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol


@dataclass
class CallContext:
    source: str
    user: str
    model_label: str                 # 呼叫端寫的完整 model(含前綴)
    session: str = ""                # X-Bridge-Session(local 用)
    dropped: list[str] = field(default_factory=list)
    served_by: str = ""
    usage: dict = field(default_factory=dict)
    job_id: str = ""                 # local:工單 id(非同步時回給呼叫端)
    wait_s: float = 0.0              # 這次同步呼叫最多等幾秒(X-Bridge-Wait;0 = 用 Bridge 預設)
    json_mode: bool = False          # 呼叫端要求 JSON 輸出(local 會拿掉模型多包的程式碼區塊外框)
    priority: str = ""               # auto:使用者選的優先(local / cloud);非 auto 為空
    fallback: dict = field(default_factory=dict)   # auto 改用備援時:{"from": 先試的 model, "reason": 錯誤代碼}


class Provider(Protocol):
    name: str

    async def complete(self, req: dict, model: str, ctx: CallContext) -> dict: ...

    def stream(self, req: dict, model: str, ctx: CallContext) -> AsyncIterator[dict]: ...
