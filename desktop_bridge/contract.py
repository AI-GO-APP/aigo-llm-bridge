from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass
from .schema_guard import check_schemas

from .errors import BridgeError

SUPPORTED = {"messages", "model", "stream", "response_format", "reasoning", "reasoning_effort", "user", "metadata", "session_id", "provider"}
NULLABLE_UNSUPPORTED = {"frequency_penalty", "logit_bias", "logprobs", "max_completion_tokens", "max_tokens",
    "min_p", "parallel_tool_calls", "prediction", "presence_penalty", "prompt_cache_key", "prompt_cache_options",
    "repetition_penalty", "route", "seed", "service_tier", "stop", "stream_options",
    "temperature", "top_a", "top_k", "top_logprobs", "top_p"}
KNOWN = SUPPORTED | NULLABLE_UNSUPPORTED | {"cache_control", "debug", "deferred_tools", "image_config", "modalities", "models", "plugins", "stop_server_tools_when", "tool_choice", "tools", "trace"}


def bad(parameter, message="此參數目前沒有等價的 CLI 實作，請移除後重試。"):
    raise BridgeError(400, "unsupported_parameter", message, parameter)


@dataclass
class Inference:
    model: dict
    messages: list
    system: str
    effort: str | None
    format: str
    schema: dict | None
    tool_proposals: bool = False
    tool_schemas: dict | None = None
    generated_schema: bool = False


def validate(body, settings, caller):
    if not isinstance(body, dict):
        raise BridgeError(400, "invalid_request", "Request 必須是 JSON object。")
    if 'tools' in body:
        from .tool_contract import proposal_request
        spec=validate(proposal_request(body),settings,caller)
        spec.tool_proposals=True
        spec.tool_schemas={t['function']['name']:t['function'].get('parameters',{'type':'object'}) for t in body['tools']}
        return spec
    for field, value in body.items():
        if field not in SUPPORTED and not (field in NULLABLE_UNSUPPORTED and value is None):
            bad(field if field in KNOWN else "unknown_field")
    # OpenRouter routing metadata is accepted for AI EA compatibility. A fixed
    # Bridge has no OpenRouter provider-selection engine; this is not a claim
    # about the signed-in subscription's data handling or a policy approval gate.
    provider = body.get("provider")
    if provider is not None:
        if not isinstance(provider, dict):
            raise BridgeError(400,"invalid_request","provider 必須是 object。","provider")
        if set(provider)-{"data_collection"}:
            bad("provider","此 Bridge 不支援這些供應商路由參數。")
        if "data_collection" in provider and provider["data_collection"] not in ("deny","allow"):
            raise BridgeError(400,"invalid_request","data_collection 必須是 deny 或 allow。","provider.data_collection")
    if "stream" in body and not isinstance(body["stream"], bool):
        raise BridgeError(400, "invalid_request", "stream 必須是 boolean。", "stream")
    if body.get("stream"):
        bad("stream", "P1 使用完整 JSON 回應；請設 stream=false。長工作可使用 /bridge/v1/jobs。")
    for name in ("user", "session_id"):
        if name in body and (not isinstance(body[name], str) or len(body[name]) > 256):
            raise BridgeError(400, "invalid_request", "識別欄位必須是最多 256 字的 string。", name)
    if "metadata" in body:
        m = body["metadata"]
        if not isinstance(m, dict) or len(m)>16 or any(not isinstance(k,str) or len(k)>64 or not isinstance(v,str) or len(v)>512 for k,v in m.items()):
            raise BridgeError(400,"invalid_request","metadata 最多 16 組；key 最多 64 字，string value 最多 512 字。","metadata")
    # Metadata, user and session_id are accepted for caller compatibility, then discarded.
    model_id = body.get("model", settings.get("default_model"))
    if not isinstance(model_id, str):
        raise BridgeError(400, "invalid_request", "model 必須是 string；可省略但不可 null。", "model")
    if model_id in {"auto", "openrouter/auto"}:
        model_id = settings.get("default_model")
    model = next((m for m in settings.get("models") if m["id"] == model_id), None)
    if model is None:
        raise BridgeError(400,"model_not_found","模型未設定；請先 GET /api/v1/models 查看可用模型。","model")
    if model["provider"] not in caller["providers"]:
        raise BridgeError(403,"forbidden","這把 key 未開放此模型來源。","model")
    messages = body.get("messages")
    if not isinstance(messages,list) or not 1 <= len(messages) <= 100:
        raise BridgeError(400,"invalid_request","messages 為必填的非空陣列，最多 100 則。","messages")
    system, turns = [], []
    for message in messages:
        if not isinstance(message,dict) or set(message)-{"role","content","name"}:
            bad("messages", "P1 訊息只支援 role 與 content；不支援 tool 訊息。")
        if "name" in message:
            bad("messages.name","P1 尚未映射訊息 name；請移除此欄位。")
        role = message.get("role")
        if not isinstance(role,str) or role not in {"system","developer","user","assistant"}:
            bad("messages.role", "P1 支援 system、developer、user、assistant；不支援 tool role。")
        content = message.get("content")
        if isinstance(content,str):
            parts = [{"type":"text","text":content}]
        elif isinstance(content,list) and content:
            parts=[]
            for part in content:
                if not isinstance(part,dict):
                    raise BridgeError(400,"invalid_request","content part 必須是 object。","messages.content")
                if part.get("type")=="text" and set(part)=={"type","text"} and isinstance(part["text"],str):
                    parts.append(part.copy())
                elif part.get("type")=="image_url" and set(part)=={"type","image_url"} and isinstance(part["image_url"],dict):
                    image = part["image_url"]
                    if set(image)-{"url","detail"} or not isinstance(image.get("detail","auto"),str) or image.get("detail","auto") not in {"auto","low","high"}:
                        bad("messages.content.image_url")
                    if image.get("detail","auto") != "auto" and model["provider"]=="claude":
                        bad("messages.content.image_url.detail")
                    url=image.get("url")
                    if not isinstance(url,str) or not re.fullmatch(r"data:image/(png|jpeg|webp|gif);base64,[A-Za-z0-9+/=]+",url):
                        bad("messages.content.image_url.url","P1 圖片請使用 base64 data URL；不會下載遠端 URL 或建立本機圖片檔。")
                    try:
                        raw=base64.b64decode(url.split(",",1)[1],validate=True)
                    except ValueError:
                        raise BridgeError(400,"invalid_request","圖片 base64 無效。","messages.content") from None
                    if not raw or len(raw)>2_000_000:
                        raise BridgeError(413,"request_too_large","單張圖片上限為 2 MB。")
                    parts.append({"type":"image_url","image_url":{"url":url,"detail":image.get("detail","auto")}})
                else:
                    bad("messages.content", "P1 content 支援文字與 image_url。")
        else:
            raise BridgeError(400,"invalid_request","content 必須是 string 或非空 content parts。","messages.content")
        if role in {"system","developer"}:
            if any(p["type"]!="text" for p in parts):
                bad("messages.content", "system／developer 僅接受文字。")
            system.append("\n".join(p["text"] for p in parts))
        else:
            if role=="assistant" and any(p["type"]!="text" for p in parts):
                bad("messages.content", "P1 assistant 歷史僅接受文字。")
            turns.append({"role":role,"parts":parts})
    if not turns or turns[-1]["role"]!="user":
        bad("messages", "最後一則非 system 訊息必須是 user。")
    if model["provider"]=="claude" and (len(turns)!=1 or turns[0]["role"]!="user"):
        bad("messages", "Claude P1 暫不支援多輪歷史；需要多輪請選 Codex 模型。")
    effort=body.get("reasoning_effort")
    if "reasoning" in body:
        reasoning=body["reasoning"]
        if not isinstance(reasoning,dict) or set(reasoning)-{"effort"}:
            bad("reasoning", "P1 reasoning 僅支援 effort。")
        other=reasoning.get("effort")
        if effort is not None and other is not None and effort!=other:
            raise BridgeError(400,"invalid_request","reasoning 與 reasoning_effort 不可互相衝突。","reasoning")
        effort=effort if effort is not None else other
    if effort is not None and (not isinstance(effort,str) or effort not in {"low","medium","high","xhigh","max"}):
        bad("reasoning_effort", "P1 effort 支援 low、medium、high、xhigh、max。")
    fmt, schema="text",None
    if "response_format" in body:
        rf=body["response_format"]
        if not isinstance(rf,dict):
            raise BridgeError(400,"invalid_request","response_format 必須是 object。","response_format")
        fmt=rf.get("type")
        if fmt=="text" and set(rf)=={"type"}:
            pass
        elif fmt=="json_object" and set(rf)=={"type"}:
            system.append("Return only a valid JSON object, without Markdown fences.")
        elif fmt=="json_schema" and set(rf)=={"type","json_schema"} and isinstance(rf["json_schema"],dict):
            js=rf["json_schema"]
            if set(js)-{"name","description","schema","strict"} or not isinstance(js.get("name"),str) or not isinstance(js.get("schema"),dict) or ("strict" in js and not isinstance(js["strict"],bool)):
                raise BridgeError(400,"invalid_request","json_schema 必須包含 name 與 schema。","response_format")
            schema=js["schema"]
            check_schemas([schema],'response_format')
            if schema.get("type")!="object" or re.search(r'"\$(?:dynamicRef|ref)"\s*:\s*"(?!#)',json.dumps(schema)):
                bad("response_format","P1 僅支援 object schema，不接受外部 schema 引用。")
        else:
            bad("response_format", "P1 支援 text、json_object、json_schema。")
    return Inference(model,turns,"\n\n".join(system),effort,fmt,schema)
