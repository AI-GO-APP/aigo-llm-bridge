import json

import pytest

from bridge.anthropic_map import (FALLBACK_BETA, StreamTranslator, from_anthropic_message, rejects_sampling,
                                  to_anthropic)
from bridge.errors import BridgeError


def req(**kw):
    base = {"messages": [{"role": "user", "content": "hi"}]}
    base.update(kw)
    return base


def test_system_messages_anywhere_become_top_level_system():
    r = req(messages=[{"role": "system", "content": "A"}, {"role": "user", "content": "q"},
                      {"role": "developer", "content": [{"type": "text", "text": "B"}]}])
    p = to_anthropic(r, "claude-opus-5", stream=False)
    assert p.kwargs["system"] == "A\n\nB"
    assert [m["role"] for m in p.kwargs["messages"]] == ["user"]


def test_default_max_tokens_depends_on_stream():
    assert to_anthropic(req(), "claude-opus-5", stream=False).kwargs["max_tokens"] == 16000
    assert to_anthropic(req(), "claude-opus-5", stream=True).kwargs["max_tokens"] == 64000
    assert to_anthropic(req(max_completion_tokens=50), "claude-opus-5", stream=False).kwargs["max_tokens"] == 50


@pytest.mark.parametrize("model,dropped", [
    ("claude-opus-5", True), ("claude-opus-5-5", True), ("claude-sonnet-5", True), ("claude-fable-5-1", True),
    ("claude-opus-4-8", True), ("claude-opus-4-7", True), ("claude-some-future-model", True),
    ("claude-haiku-4-5", False), ("claude-sonnet-4-6", False), ("claude-opus-4-6", False),
])
def test_sampling_params_dropped_on_models_that_reject_them(model, dropped):
    p = to_anthropic(req(temperature=0.2, top_p=0.9), model, stream=False)
    assert rejects_sampling(model) is dropped
    assert ("temperature" in p.kwargs) is (not dropped)
    assert (p.dropped == ["temperature", "top_p"]) is dropped


def test_trailing_assistant_prefill_rejected():
    with pytest.raises(BridgeError) as e:
        to_anthropic(req(messages=[{"role": "user", "content": "q"}, {"role": "assistant", "content": "{"}]),
                     "claude-opus-5", stream=False)
    assert e.value.code == "prefill_not_supported"


def test_json_schema_maps_to_output_config_and_effort_shares_it():
    schema = {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"],
              "additionalProperties": False}
    p = to_anthropic(req(response_format={"type": "json_schema", "json_schema": {"name": "x", "schema": schema}},
                         reasoning_effort="low"), "claude-opus-5", stream=False)
    assert p.kwargs["output_config"] == {"effort": "low", "format": {"type": "json_schema", "schema": schema}}


def test_json_object_adds_instruction_instead_of_prefill():
    p = to_anthropic(req(response_format={"type": "json_object"}), "claude-opus-5", stream=False)
    assert "JSON" in p.kwargs["system"]
    assert "output_config" not in p.kwargs


def test_fallbacks_only_for_exact_models_and_can_be_disabled():
    assert to_anthropic(req(), "claude-opus-5", stream=False).betas == [FALLBACK_BETA]
    assert to_anthropic(req(), "claude-opus-5", stream=False).extra_body == {"fallbacks": "default"}
    assert to_anthropic(req(), "claude-opus-5-5", stream=False).betas == []
    assert to_anthropic(req(), "claude-sonnet-5", stream=False).betas == []
    assert to_anthropic(req(), "claude-opus-5", stream=False, fallbacks=False).betas == []


def test_tools_and_tool_round_trip():
    msgs = [
        {"role": "user", "content": "weather?"},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "call_1", "type": "function", "function": {"name": "get", "arguments": '{"city":"Taipei"}'}},
            {"id": "call_2", "type": "function", "function": {"name": "get", "arguments": '{"city":"Tokyo"}'}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "sunny"},
        {"role": "tool", "tool_call_id": "call_2", "content": "rain"},
    ]
    tools = [{"type": "function", "function": {"name": "get", "parameters": {"type": "object"}, "strict": True}}]
    p = to_anthropic(req(messages=msgs, tools=tools, parallel_tool_calls=False), "claude-opus-5", stream=False)
    m = p.kwargs["messages"]
    assert [x["role"] for x in m] == ["user", "assistant", "user"]
    assert [b["type"] for b in m[1]["content"]] == ["tool_use", "tool_use"]
    assert m[1]["content"][0]["input"] == {"city": "Taipei"}
    # 兩個工具結果必須在同一則 user 訊息裡
    assert [b["tool_use_id"] for b in m[2]["content"]] == ["call_1", "call_2"]
    assert p.kwargs["tools"][0] == {"name": "get", "description": "", "input_schema": {"type": "object"}, "strict": True}
    assert p.kwargs["tool_choice"] == {"type": "auto", "disable_parallel_tool_use": True}


def test_forced_tool_choice_rejected_early_on_models_without_it():
    tools = [{"type": "function", "function": {"name": "get", "parameters": {"type": "object"}}}]
    with pytest.raises(BridgeError) as e:
        to_anthropic(req(tools=tools, tool_choice="required"), "claude-opus-5-5", stream=False)
    assert e.value.code == "forced_tool_unsupported"
    ok = to_anthropic(req(tools=tools, tool_choice="required"), "claude-opus-5", stream=False)
    assert ok.kwargs["tool_choice"] == {"type": "any"}


def test_images_data_url_and_https_only():
    content = [{"type": "text", "text": "what?"},
               {"type": "image_url", "image_url": {"url": "data:image/png;base64,QUJD"}},
               {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}}]
    blocks = to_anthropic(req(messages=[{"role": "user", "content": content}]), "claude-opus-5",
                          stream=False).kwargs["messages"][0]["content"]
    assert blocks[1]["source"] == {"type": "base64", "media_type": "image/png", "data": "QUJD"}
    assert blocks[2]["source"] == {"type": "url", "url": "https://example.com/a.png"}
    with pytest.raises(BridgeError):
        to_anthropic(req(messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": "http://insecure/a.png"}}]}]), "claude-opus-5", stream=False)


def test_user_field_is_hashed():
    p = to_anthropic(req(user="alice@example.com"), "claude-opus-5", stream=False)
    assert "alice" not in json.dumps(p.kwargs)
    assert len(p.kwargs["metadata"]["user_id"]) == 32


def test_message_to_openai_with_refusal_and_usage():
    msg = {"id": "msg_1", "model": "claude-opus-4-8", "stop_reason": "refusal",
           "stop_details": {"category": "cyber", "explanation": "nope"},
           "content": [{"type": "thinking", "thinking": ""}, {"type": "text", "text": ""}],
           "usage": {"input_tokens": 10, "cache_read_input_tokens": 90, "output_tokens": 5}}
    out = from_anthropic_message(msg, "anthropic/claude-opus-5")
    assert out["choices"][0]["finish_reason"] == "content_filter"
    assert out["choices"][0]["message"]["refusal"] == "nope"
    assert out["usage"] == {"prompt_tokens": 100, "completion_tokens": 5, "total_tokens": 105,
                            "prompt_tokens_details": {"cached_tokens": 90}}
    assert out["served_by"] == "claude-opus-4-8"


def test_message_with_tool_use():
    msg = {"id": "m", "stop_reason": "tool_use",
           "content": [{"type": "tool_use", "id": "toolu_1", "name": "get", "input": {"city": "台北"}}]}
    choice = from_anthropic_message(msg, "x")["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["content"] is None
    assert json.loads(choice["message"]["tool_calls"][0]["function"]["arguments"]) == {"city": "台北"}


def test_stream_translation():
    tr = StreamTranslator("anthropic/claude-opus-5", include_usage=True)
    events = [
        {"type": "message_start", "message": {"usage": {"input_tokens": 7}}},
        {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking"}},
        {"type": "content_block_delta", "index": 0, "delta": {"type": "thinking_delta", "thinking": "hmm"}},
        {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}},
        {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "你"}},
        {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "好"}},
        {"type": "content_block_start", "index": 2, "content_block": {"type": "tool_use", "id": "t1", "name": "get"}},
        {"type": "content_block_delta", "index": 2, "delta": {"type": "input_json_delta", "partial_json": '{"a":'}},
        {"type": "message_delta", "delta": {"stop_reason": "tool_use"}, "usage": {"output_tokens": 3}},
        {"type": "message_stop"},
    ]
    chunks = [c for e in events for c in tr.feed(e)]
    deltas = [c["choices"][0]["delta"] for c in chunks]
    assert deltas[0] == {"role": "assistant", "content": ""}
    assert "".join(d.get("content", "") for d in deltas) == "你好"
    assert "hmm" not in json.dumps(chunks, ensure_ascii=False)
    assert deltas[3]["tool_calls"][0]["function"]["name"] == "get"
    assert deltas[4]["tool_calls"][0]["function"]["arguments"] == '{"a":'
    assert chunks[-1]["choices"][0]["finish_reason"] == "tool_calls"
    assert chunks[-1]["usage"]["prompt_tokens"] == 7 and chunks[-1]["usage"]["completion_tokens"] == 3
    assert tr.text == "你好"
