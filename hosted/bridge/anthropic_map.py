"""OpenAI Chat Completions ⇄ Anthropic Messages 的翻譯(純函式,不碰網路)。

規則見 docs/09-api-reference.md §2.1、§2.2。這裡只處理「形狀」;呼叫與錯誤處理在 providers/anthropic.py。
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field

from .errors import BridgeError
from .reasoning import can_disable_thinking, supports_effort, uses_budget_thinking
from .reasoning import normalize as normalize_reasoning

DEFAULT_MAX_TOKENS_SYNC = 16000
DEFAULT_MAX_TOKENS_STREAM = 64000

# 仍接受 temperature / top_p / top_k 的模型(舊世代)。其餘一律視為會以 400 拒收:
# 新模型的趨勢是拒收,未知的新模型也照「拒收」處理,寧可少傳一個參數也不要整個請求失敗。
_SAMPLING_OK = re.compile(r"^claude-(3|haiku-4-5|sonnet-4-5|opus-4-5|opus-4-1|sonnet-4-6|opus-4-6|sonnet-4-2|opus-4-2)")
# 不接受「強制使用工具」(tool_choice any / tool)的模型
_NO_FORCED_TOOL = ("claude-fable-5-1", "claude-mythos-5-1", "claude-opus-5-5")
# 預設帶「拒答後備」的模型(精確比對:claude-opus-5 不含 claude-opus-5-5)
_FALLBACK_DEFAULT = ("claude-opus-5", "claude-fable-5-1")
FALLBACK_BETA = "server-side-fallback-2026-07-01"

_DATA_URL = re.compile(r"^data:(image/[a-zA-Z0-9.+-]+);base64,(.+)$", re.S)

_FINISH = {"end_turn": "stop", "stop_sequence": "stop", "max_tokens": "length",
           "tool_use": "tool_calls", "refusal": "content_filter", "pause_turn": "stop"}


def rejects_sampling(model: str) -> bool:
    return not _SAMPLING_OK.match(model)


@dataclass
class Prepared:
    kwargs: dict
    betas: list[str] = field(default_factory=list)
    extra_body: dict = field(default_factory=dict)
    dropped: list[str] = field(default_factory=list)


def _text_of(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if isinstance(part, dict) and part.get("type") in ("text", "input_text", "output_text"):
            parts.append(str(part.get("text") or ""))
    return "".join(parts)


def _user_blocks(content) -> list[dict]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}] if content else []
    blocks = []
    for part in content or []:
        if not isinstance(part, dict):
            continue
        kind = part.get("type")
        if kind in ("text", "input_text"):
            blocks.append({"type": "text", "text": str(part.get("text") or "")})
        elif kind in ("image_url", "input_image"):
            raw = part.get("image_url")
            url = raw.get("url") if isinstance(raw, dict) else raw
            url = str(url or "")
            match = _DATA_URL.match(url)
            if match:
                blocks.append({"type": "image", "source": {"type": "base64", "media_type": match.group(1),
                                                           "data": match.group(2)}})
            elif url.startswith("https://"):
                blocks.append({"type": "image", "source": {"type": "url", "url": url}})
            else:
                raise BridgeError(400, "bad_image", "圖片只接受 https 網址或 data URL")
        else:
            raise BridgeError(400, "unsupported_content", f"不支援的內容類型:{kind}")
    return blocks


def _append(messages: list[dict], role: str, blocks: list[dict]) -> None:
    """相鄰同角色的訊息併成一則(工具結果一定要在同一則 user 訊息裡回)。"""
    if not blocks:
        return
    if messages and messages[-1]["role"] == role:
        messages[-1]["content"].extend(blocks)
    else:
        messages.append({"role": role, "content": list(blocks)})


def _convert_messages(raw: list) -> tuple[str, list[dict]]:
    system_parts: list[str] = []
    messages: list[dict] = []
    for msg in raw or []:
        if not isinstance(msg, dict):
            raise BridgeError(400, "bad_messages", "messages 的每一項都要是物件")
        role = msg.get("role")
        if role in ("system", "developer"):
            text = _text_of(msg.get("content"))
            if text:
                system_parts.append(text)
        elif role == "user":
            _append(messages, "user", _user_blocks(msg.get("content")))
        elif role == "assistant":
            blocks = []
            text = _text_of(msg.get("content"))
            if text:
                blocks.append({"type": "text", "text": text})
            for call in msg.get("tool_calls") or []:
                fn = call.get("function") or {}
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    raise BridgeError(400, "bad_tool_arguments", "tool_calls 的 arguments 不是合法 JSON")
                blocks.append({"type": "tool_use", "id": call.get("id") or f"toolu_{uuid.uuid4().hex[:20]}",
                               "name": fn.get("name") or "", "input": args})
            _append(messages, "assistant", blocks)
        elif role == "tool":
            _append(messages, "user", [{"type": "tool_result", "tool_use_id": msg.get("tool_call_id") or "",
                                        "content": _text_of(msg.get("content"))}])
        else:
            raise BridgeError(400, "bad_role", f"不支援的角色:{role}")
    if not messages:
        raise BridgeError(400, "empty_messages", "至少要有一則 user 訊息")
    if messages[0]["role"] != "user":
        raise BridgeError(400, "bad_messages", "第一則非系統訊息必須是 user")
    if messages[-1]["role"] == "assistant":
        raise BridgeError(400, "prefill_not_supported",
                          "最後一則不能是 assistant(目前世代的模型不接受預填);要固定輸出格式請改用 response_format")
    return "\n\n".join(system_parts), messages


def _convert_tools(tools: list, tool_choice, parallel, model: str) -> tuple[list[dict], dict | None]:
    out = []
    for tool in tools or []:
        if not isinstance(tool, dict) or tool.get("type") not in (None, "function"):
            raise BridgeError(400, "unsupported_tool", "只支援 function 類型的工具")
        fn = tool.get("function") or {}
        entry = {"name": fn.get("name") or "", "description": fn.get("description") or "",
                 "input_schema": fn.get("parameters") or {"type": "object", "properties": {}}}
        if fn.get("strict"):
            entry["strict"] = True
        out.append(entry)

    choice = None
    if tool_choice in (None, "auto"):
        choice = {"type": "auto"} if out else None
    elif tool_choice == "none":
        choice = {"type": "none"}
    elif tool_choice == "required":
        choice = {"type": "any"}
    elif isinstance(tool_choice, dict) and (tool_choice.get("function") or {}).get("name"):
        choice = {"type": "tool", "name": tool_choice["function"]["name"]}
    else:
        raise BridgeError(400, "bad_tool_choice", "tool_choice 只接受 auto / none / required / 指定函式")
    if choice and choice["type"] in ("any", "tool") and model.startswith(_NO_FORCED_TOOL):
        raise BridgeError(400, "forced_tool_unsupported",
                          f"{model} 不支援強制使用工具;請改用 tool_choice=auto 並在提示中指明要用哪個工具")
    if choice and parallel is False and choice["type"] != "none":
        choice["disable_parallel_tool_use"] = True
    return out, choice


def to_anthropic(req: dict, model: str, *, stream: bool, fallbacks: bool = True) -> Prepared:
    system, messages = _convert_messages(req.get("messages"))
    prep = Prepared(kwargs={"model": model, "messages": messages})
    kw = prep.kwargs

    max_tokens = req.get("max_completion_tokens") or req.get("max_tokens")
    kw["max_tokens"] = int(max_tokens) if max_tokens else (
        DEFAULT_MAX_TOKENS_STREAM if stream else DEFAULT_MAX_TOKENS_SYNC)

    stop = req.get("stop")
    if stop:
        kw["stop_sequences"] = [stop] if isinstance(stop, str) else list(stop)

    for name in ("temperature", "top_p", "top_k"):
        if req.get(name) is not None:
            if rejects_sampling(model):
                prep.dropped.append(name)
            else:
                kw[name] = req[name]

    # 思考與 effort:呼叫端沒指定就不送,照模型原本的行為(docs/01 S1b);指定了但模型不支援的記進 dropped
    output_config: dict = {}
    thinking = normalize_reasoning(req)
    if thinking["effort"]:
        if supports_effort(model):
            output_config["effort"] = thinking["effort"]
        else:
            prep.dropped.append("reasoning_effort")
    if thinking["thinking"] == "off":
        if uses_budget_thinking(model):
            pass                                   # 舊世代:不帶 thinking 就是不思考
        elif can_disable_thinking(model, thinking["effort"]):
            kw["thinking"] = {"type": "disabled"}
        else:
            prep.dropped.append("thinking_off")    # Opus 5.5、Fable 關不掉,只能靠 effort
    elif thinking["thinking"] == "on":
        if uses_budget_thinking(model):
            budget = min(max(thinking["budget"] or 4096, 1024), kw["max_tokens"] - 1)
            if budget >= 1024:
                kw["thinking"] = {"type": "enabled", "budget_tokens": budget}
            else:
                prep.dropped.append("thinking_on")  # max_tokens 太小,放不下最低 1024 的思考預算
        else:
            kw["thinking"] = {"type": "adaptive"}

    fmt = req.get("response_format") or {}
    if fmt.get("type") == "json_schema":
        schema = (fmt.get("json_schema") or {}).get("schema")
        if not isinstance(schema, dict):
            raise BridgeError(400, "bad_response_format", "response_format.json_schema.schema 必填")
        output_config["format"] = {"type": "json_schema", "schema": schema}
    elif fmt.get("type") == "json_object":
        system = (system + "\n\n" if system else "") + "只輸出一個合法的 JSON 物件,不要加任何說明文字或程式碼區塊標記。"
    if output_config:
        kw["output_config"] = output_config
    if system:
        kw["system"] = system

    tools, choice = _convert_tools(req.get("tools"), req.get("tool_choice"), req.get("parallel_tool_calls"), model)
    if tools:
        kw["tools"] = tools
    if choice:
        kw["tool_choice"] = choice

    if req.get("user"):
        kw["metadata"] = {"user_id": hashlib.sha256(str(req["user"]).encode()).hexdigest()[:32]}

    if fallbacks and model in _FALLBACK_DEFAULT:
        prep.betas.append(FALLBACK_BETA)
        prep.extra_body["fallbacks"] = "default"
    return prep


def usage_to_openai(usage: dict | None) -> dict:
    usage = usage or {}
    cached = int(usage.get("cache_read_input_tokens") or 0)
    prompt = int(usage.get("input_tokens") or 0) + cached + int(usage.get("cache_creation_input_tokens") or 0)
    completion = int(usage.get("output_tokens") or 0)
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": prompt + completion,
            "prompt_tokens_details": {"cached_tokens": cached}}


def finish_reason(stop_reason: str | None) -> str | None:
    return _FINISH.get(stop_reason or "", "stop") if stop_reason else None


def from_anthropic_message(msg: dict, model_label: str) -> dict:
    text, calls = [], []
    for block in msg.get("content") or []:
        kind = block.get("type")
        if kind == "text":
            text.append(block.get("text") or "")
        elif kind == "tool_use":
            calls.append({"id": block.get("id"), "type": "function",
                          "function": {"name": block.get("name"),
                                       "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False)}})
    message: dict = {"role": "assistant", "content": "".join(text) if text or not calls else None}
    if calls:
        message["tool_calls"] = calls
    stop_reason = msg.get("stop_reason")
    if stop_reason == "refusal":
        details = msg.get("stop_details") or {}
        message["refusal"] = details.get("explanation") or "模型拒絕回答這個請求"
    choice = {"index": 0, "message": message, "finish_reason": finish_reason(stop_reason) or "stop"}
    out = {"id": "chatcmpl-" + str(msg.get("id") or uuid.uuid4().hex), "object": "chat.completion",
           "created": int(time.time()), "model": model_label, "choices": [choice],
           "usage": usage_to_openai(msg.get("usage"))}
    if stop_reason == "refusal":
        out["stop_details"] = {"category": (msg.get("stop_details") or {}).get("category")}
    if msg.get("model"):
        out["served_by"] = msg["model"]   # 拒答後備啟動時,實際回答的模型可能不同
    return out


class StreamTranslator:
    """把 Anthropic 串流事件(dict)逐一翻成 OpenAI chat.completion.chunk。"""

    def __init__(self, model_label: str, include_usage: bool = False):
        self.model_label = model_label
        self.include_usage = include_usage
        self.id = "chatcmpl-" + uuid.uuid4().hex
        self.created = int(time.time())
        self.usage: dict = {}
        self.tool_index: dict[int, int] = {}   # Anthropic 區塊序號 → OpenAI tool_calls 序號
        self.sent_role = False
        self.stop_reason: str | None = None
        self.text_parts: list[str] = []

    def _chunk(self, delta: dict, finish: str | None = None) -> dict:
        return {"id": self.id, "object": "chat.completion.chunk", "created": self.created,
                "model": self.model_label, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}

    def _with_role(self, delta: dict) -> dict:
        if not self.sent_role:
            self.sent_role = True
            return {"role": "assistant", **delta}
        return delta

    def feed(self, event: dict) -> list[dict]:
        kind = event.get("type")
        if kind == "message_start":
            message = event.get("message") or {}
            self.usage.update(message.get("usage") or {})
            return [self._chunk(self._with_role({"content": ""}))]
        if kind == "content_block_start":
            block = event.get("content_block") or {}
            if block.get("type") == "tool_use":
                idx = len(self.tool_index)
                self.tool_index[event.get("index", 0)] = idx
                return [self._chunk(self._with_role({"tool_calls": [{
                    "index": idx, "id": block.get("id"), "type": "function",
                    "function": {"name": block.get("name"), "arguments": ""}}]}))]
            return []
        if kind == "content_block_delta":
            delta = event.get("delta") or {}
            if delta.get("type") == "text_delta":
                self.text_parts.append(delta.get("text") or "")
                return [self._chunk(self._with_role({"content": delta.get("text") or ""}))]
            if delta.get("type") == "input_json_delta":
                idx = self.tool_index.get(event.get("index", 0), 0)
                return [self._chunk({"tool_calls": [{"index": idx,
                                                     "function": {"arguments": delta.get("partial_json") or ""}}]})]
            return []   # thinking / signature 等不輸出
        if kind == "message_delta":
            self.stop_reason = (event.get("delta") or {}).get("stop_reason") or self.stop_reason
            self.usage.update({k: v for k, v in (event.get("usage") or {}).items() if v is not None})
            return []
        if kind == "message_stop":
            final = self._chunk({}, finish_reason(self.stop_reason) or "stop")
            if self.include_usage:
                final["usage"] = usage_to_openai(self.usage)
            return [final]
        return []

    @property
    def text(self) -> str:
        return "".join(self.text_parts)
