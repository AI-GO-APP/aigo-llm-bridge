"""把呼叫端三種「思考」寫法統一成一種,再依模型決定實際怎麼送。

接受的寫法(可混用,後面的蓋前面的):
  OpenAI      reasoning_effort: minimal | low | medium | high | xhigh | max | none
  OpenRouter  reasoning: {effort, enabled, max_tokens}      effort 另有 minimal、none
  Anthropic   thinking: {type: adaptive | enabled | disabled, budget_tokens}
統一後:{"effort": low..max 或 None, "thinking": "on" | "off" | None, "budget": int 或 None}
None 代表「呼叫端沒指定 → 照模型原本的行為」。預設永遠是 None,Bridge 不替呼叫端決定(docs/01 S1b)。
"""

from __future__ import annotations

import re

from .errors import BridgeError

EFFORTS = ("low", "medium", "high", "xhigh", "max")

# 規則來源:Anthropic 模型文件與 Claude Code 模型設定文件(見 docs/09 §2.4)
_NO_EFFORT = re.compile(r"^claude-(3|haiku-4-5|sonnet-4-5|opus-4-5|opus-4-1|sonnet-4-2|opus-4-2)")
_CANNOT_DISABLE = re.compile(r"^claude-(opus-5-5|fable|mythos)")
_BUDGET_THINKING = re.compile(r"^claude-(3-7|haiku-4-5|sonnet-4-5|opus-4-5|opus-4-1|sonnet-4-2|opus-4-2)")


def _effort(value) -> tuple[str | None, str | None]:
    """回 (effort, thinking)。minimal 視為 low;none 視為關閉思考。"""
    if value in (None, ""):
        return None, None
    value = str(value).lower()
    if value == "none":
        return None, "off"
    if value == "minimal":
        return "low", None
    if value not in EFFORTS:
        raise BridgeError(400, "bad_reasoning_effort", f"effort 只接受 minimal、none 或 {', '.join(EFFORTS)}")
    return value, None


def normalize(req: dict) -> dict:
    out: dict = {"effort": None, "thinking": None, "budget": None}

    effort, thinking = _effort(req.get("reasoning_effort"))
    out["effort"], out["thinking"] = effort or out["effort"], thinking or out["thinking"]

    reasoning = req.get("reasoning")
    if isinstance(reasoning, dict):
        effort, thinking = _effort(reasoning.get("effort"))
        out["effort"], out["thinking"] = effort or out["effort"], thinking or out["thinking"]
        if reasoning.get("enabled") is False:
            out["thinking"] = "off"
        elif reasoning.get("enabled") is True and out["thinking"] is None:
            out["thinking"] = "on"
        if isinstance(reasoning.get("max_tokens"), int):
            out["budget"], out["thinking"] = reasoning["max_tokens"], out["thinking"] or "on"

    thinking_param = req.get("thinking")
    if isinstance(thinking_param, dict):
        kind = thinking_param.get("type")
        if kind == "disabled":
            out["thinking"] = "off"
        elif kind in ("adaptive", "enabled"):
            out["thinking"] = "on"
            if isinstance(thinking_param.get("budget_tokens"), int):
                out["budget"] = thinking_param["budget_tokens"]

    if out["thinking"] == "off":
        out["budget"] = None
    return out


def supports_effort(model: str) -> bool:
    return not _NO_EFFORT.match(model)


def can_disable_thinking(model: str, effort: str | None) -> bool:
    if _CANNOT_DISABLE.match(model):
        return False
    if model == "claude-opus-5" and effort in ("xhigh", "max"):
        return False   # Opus 5 只有在 effort ≤ high 時接受關閉思考
    return True


def uses_budget_thinking(model: str) -> bool:
    """舊世代模型的思考用固定預算(budget_tokens);新模型用 adaptive。"""
    return bool(_BUDGET_THINKING.match(model))
