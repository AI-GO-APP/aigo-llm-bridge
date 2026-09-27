import importlib
import json
import sys
import uuid
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FAKE = [sys.executable, str(HERE / "fake_claude.py")]


@pytest.fixture()
def w(tmp_path, monkeypatch):
    monkeypatch.setenv("AIGO_BRIDGE_WORKER_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    sys.path.insert(0, str(HERE.parent))
    import aigo_bridge_worker as mod
    mod = importlib.reload(mod)
    calls = []
    monkeypatch.setattr(mod, "call", lambda base, path, body=None, key="", timeout=40: calls.append((path, body)) or {})
    monkeypatch.setattr(mod, "CHUNK_EVERY_S", 0)
    mod.calls = calls
    return mod


def make_worker(mod):
    return mod.Worker({"bridge_url": "https://bridge.test", "device_key": "bwk_x"}, claude=FAKE)


def test_preflight_rejects_not_logged_in_and_token_mode(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_LOGGED_IN", "0")
    with pytest.raises(SystemExit, match="尚未登入"):
        w.preflight(FAKE)
    monkeypatch.setenv("FAKE_CLAUDE_LOGGED_IN", "1")
    assert w.preflight(FAKE)["email"] == "owner@example.com"
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "x")
    with pytest.raises(SystemExit, match="長效 token"):
        w.preflight(FAKE)


def test_stream_job_redacts_and_reports(w, monkeypatch, tmp_path):
    run_dir = str(w.RUN_DIR)
    secret = f"我的 email 是 owner@example.com,同事 bob@example.com,外部 x@other.org,工作目錄 {run_dir}。結尾文字補足長度。"
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", secret)
    args_out = tmp_path / "args.json"
    monkeypatch.setenv("FAKE_CLAUDE_ARGS_OUT", str(args_out))
    worker = make_worker(w)
    worker.run_job({"job_id": "j1", "alias": "haiku", "system": "你是助理", "prompt": "問題"})

    chunks = [b["text"] for p, b in w.calls if p.endswith("/chunk")]
    result = next(b for p, b in w.calls if p.endswith("/result"))
    for text in chunks + [result["text"]]:
        assert "owner@example.com" not in text and "bob@example.com" not in text and run_dir not in text
    assert "x@other.org" in result["text"]                       # 外部網域不遮
    assert all(result["text"].startswith(c) for c in chunks)     # 逐段都是全文的前綴
    assert result["usage"] == {"input_tokens": 12, "output_tokens": 7}
    assert result["model"] == "claude-haiku-4-5"

    sent = json.loads(args_out.read_text(encoding="utf-8"))
    a = sent["args"]
    assert a[a.index("--tools") + 1] == ""                       # 空字串參數原樣送到
    assert "--no-session-persistence" in a and json.loads(a[a.index("--settings") + 1]) == {"alwaysThinkingEnabled": False}
    assert a[a.index("--system-prompt") + 1].startswith("你是助理") and "不要在回答中提及" in a[a.index("--system-prompt") + 1]
    assert sent["stdin"] == "問題"


def test_opus_uses_low_effort_instead_of_disabling_thinking(w):
    cmd, streaming = w.build_command(FAKE, {"alias": "opus"}, {})
    assert "--effort" in cmd and cmd[cmd.index("--effort") + 1] == "low" and "--settings" not in cmd
    cmd, _ = w.build_command(FAKE, {"alias": "sonnet", "effort": "high"}, {})
    assert cmd[cmd.index("--effort") + 1] == "high"


def test_session_first_then_resume(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "嗨" * 50)
    sid = str(uuid.uuid4())
    cmd, _ = w.build_command(FAKE, {"session": sid}, {})
    assert cmd[cmd.index("--session-id") + 1] == sid
    worker = make_worker(w)
    worker.run_job({"job_id": "j2", "session": sid, "prompt": "p"})
    cmd, _ = w.build_command(FAKE, {"session": sid}, worker.sessions)
    assert cmd[cmd.index("--resume") + 1] == sid
    with pytest.raises(ValueError):
        w.build_command(FAKE, {"session": "not-a-uuid"}, {})


def test_json_schema_job_returns_structured(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "")
    worker = make_worker(w)
    worker.run_job({"job_id": "j3", "prompt": "p", "json_schema": {"type": "object"}})
    result = next(b for p, b in w.calls if p.endswith("/result"))
    assert result["structured"] == {"answer": "ok"}


def test_failure_is_reported(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "x")
    monkeypatch.setenv("FAKE_CLAUDE_FAIL", "1")
    worker = make_worker(w)
    worker.run_job({"job_id": "j4", "prompt": "p"})
    assert any(p.endswith("/fail") for p, _ in w.calls)
    assert not any(p.endswith("/result") for p, _ in w.calls)


def test_bad_alias_fails_job_without_running(w):
    worker = make_worker(w)
    worker.run_job({"job_id": "j5", "alias": "gpt", "prompt": "p"})
    assert w.calls == [("/worker/jobs/j5/fail", {"code": "bad_job", "message": "不認得的模型別名 gpt"})]
