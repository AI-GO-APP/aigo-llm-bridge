"""`model: "auto"`:依使用者自己選的優先順序,在「本機 Claude Code」與「雲端」之間主備切換。

規則(docs/05 §3、docs/09 §2.6):
- 兩個候選:一個 `local/*`、一個雲端(`openrouter/*` 或 `anthropic/*`)。來源依序是請求的 `models`、
  Bridge 設定 `BRIDGE_AUTO_LOCAL` / `BRIDGE_AUTO_CLOUD`。
- 優先順序是**使用者自己選的**,依「app(source)× 使用者」存在 Bridge。還沒選過就回 409
  `priority_required`,**不套任何預設** —— 由 app 在第一次使用時問使用者。
- 先試優先的那個;只有「換一個後端可能就會成功」的錯誤才改用另一個(見 FALLBACK_CODES)。
  請求本身有問題(參數不合法、模型名稱錯)換後端也一樣錯,直接回報。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .config import Settings
from .errors import BridgeError
from .store import Store, now

PRIORITIES = ("local", "cloud")
LABELS = {"local": "我的電腦(Claude Code)", "cloud": "雲端(OpenRouter)"}

# 換一個後端就可能成功的錯誤。其餘(400 類、驗證失敗)不切換,原樣回報。
FALLBACK_CODES = frozenset({
    # 本機這一側
    "no_worker_for_user", "worker_offline", "worker_timeout", "worker_failed", "failed", "job_missing",
    "claude_exit", "claude_error", "claude_incomplete", "claude_bad_output",
    # 雲端這一側
    "provider_not_configured", "provider_unreachable", "provider_rate_limited", "provider_auth",
    "provider_billing", "provider_error",
})


def can_fall_back(code: str | None) -> bool:
    return (code or "") in FALLBACK_CODES


@dataclass(frozen=True)
class Candidates:
    local: str          # 例 local/self、local/self:sonnet
    cloud: str          # 例 openrouter/anthropic/claude-sonnet-4.5;空字串 = 沒有雲端候選

    def ordered(self, priority: str) -> list[tuple[str, str]]:
        """回 [(側, model), ...],優先的在前;沒有雲端候選時只剩本機。"""
        pairs = [("local", self.local), ("cloud", self.cloud)]
        if priority == "cloud":
            pairs.reverse()
        return [(side, model) for side, model in pairs if model]


def side_of(model: str) -> str:
    prefix = (model or "").partition("/")[0]
    if prefix == "local":
        return "local"
    if prefix in ("openrouter", "anthropic"):
        return "cloud"
    raise BridgeError(400, "bad_auto_models",
                      f"auto 的候選只能是 local/*、openrouter/* 或 anthropic/*,收到「{model}」")


def candidates(req: dict, settings: Settings) -> Candidates:
    local, cloud = settings.auto_local_model, settings.auto_cloud_model
    listed = req.get("models")
    if listed is not None:
        if not isinstance(listed, list) or not all(isinstance(m, str) and m.strip() for m in listed):
            raise BridgeError(400, "bad_auto_models", "models 要是模型名稱的陣列")
        sides: dict[str, str] = {}
        for model in listed:
            side = side_of(model.strip())
            if side in sides:
                raise BridgeError(400, "bad_auto_models", "auto 的 models 只能各放一個本機與一個雲端模型")
            sides[side] = model.strip()
        local, cloud = sides.get("local", local), sides.get("cloud", cloud)
    if not local:
        raise BridgeError(400, "bad_auto_models", "auto 需要一個本機候選(models 裡的 local/*,或設定 BRIDGE_AUTO_LOCAL)")
    return Candidates(local=local, cloud=cloud)


def _pref_key(source: str, owner: str) -> str:
    return hashlib.sha256(f"pref|{source}|{owner}".encode()).hexdigest()[:32]


class Preferences:
    """使用者自己選的優先順序,依 app(source)× 使用者存一筆。"""

    def __init__(self, store: Store):
        self.store = store

    async def get(self, source: str, owner: str) -> dict | None:
        if not owner:
            return None
        return await self.store.by_key("prefs", _pref_key(source, owner))

    async def priority(self, source: str, owner: str) -> str:
        row = await self.get(source, owner)
        value = (row or {}).get("priority")
        if value not in PRIORITIES:
            raise BridgeError(409, "priority_required",
                              "還沒選擇優先使用哪一個。請先讓使用者在「我的電腦(Claude Code)」與「雲端(OpenRouter)」"
                              "之間選一個優先,另一個會自動當備援(PUT /bridge/preferences)")
        return value

    async def set(self, source: str, owner: str, priority: str) -> dict:
        if priority not in PRIORITIES:
            raise BridgeError(400, "bad_priority", "priority 只能是 local 或 cloud")
        if not owner:
            raise BridgeError(400, "user_required", "偏好要屬於某位使用者(X-Bridge-User 或 session token)")
        row = await self.get(source, owner)
        data = {"priority": priority, "updated_ts": now()}
        if row:
            return await self.store.update("prefs", row, data)
        return await self.store.insert("prefs", {"key": _pref_key(source, owner), "owner": owner, "source": source,
                                                 **data})
