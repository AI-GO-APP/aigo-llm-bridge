"""測試用的假 claude:照 Claude Code 的輸出形狀吐固定內容,不連網、不用帳號。

環境變數控制行為:
  FAKE_CLAUDE_LOGGED_IN=0   auth status 回未登入
  FAKE_CLAUDE_TEXT          要「生成」的文字(預設含 email 與路徑,用來測遮罩)
  FAKE_CLAUDE_FAIL=1        result 事件標 is_error
  FAKE_CLAUDE_ARGS_OUT      把收到的參數寫到這個檔
"""
import json
import os
import sys

args = sys.argv[1:]
if os.environ.get("FAKE_CLAUDE_ARGS_OUT"):
    with open(os.environ["FAKE_CLAUDE_ARGS_OUT"], "w", encoding="utf-8") as f:
        json.dump({"args": args, "stdin": None if args[:1] == ["auth"] else sys.stdin.buffer.read().decode("utf-8")},
                  f, ensure_ascii=False)

if args[:2] == ["auth", "status"]:
    print(json.dumps({"loggedIn": os.environ.get("FAKE_CLAUDE_LOGGED_IN", "1") == "1", "authMethod": "claude.ai",
                      "email": "owner@example.com"}))
    sys.exit(0)


def out(obj):
    # 真正的 Claude Code 一律輸出 UTF-8;不要依賴主控台編碼
    sys.stdout.buffer.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()


text = os.environ.get("FAKE_CLAUDE_TEXT", "")
fail = os.environ.get("FAKE_CLAUDE_FAIL") == "1"
usage = {"input_tokens": 12, "output_tokens": 7}
model_usage = {"claude-haiku-4-5": {}}

if "--json-schema" in args:
    out({"type": "result", "is_error": fail, "result": text or "{}", "structured_output": {"answer": text or "ok"},
         "usage": usage, "total_cost_usd": 0.0004, "session_id": "s", "modelUsage": model_usage})
    sys.exit(1 if fail else 0)

out({"type": "system", "subtype": "init", "tools": []})
for i in range(0, len(text), 5):
    out({"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta",
                                                                                     "text": text[i:i + 5]}}})
out({"type": "stream_event", "event": {"type": "message_stop"}})
out({"type": "result", "subtype": "success", "is_error": fail, "result": "boom" if fail else text,
     "usage": usage, "total_cost_usd": 0.0009, "session_id": "sess-1", "modelUsage": model_usage})
sys.exit(0)
