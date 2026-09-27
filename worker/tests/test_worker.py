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
    worker.run_job({"job_id": "j1", "model": "haiku", "system": "你是助理", "prompt": "問題"})

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
    assert "--no-session-persistence" in a
    assert "--settings" not in a and "--effort" not in a            # 沒指定就不替呼叫端決定
    assert a[a.index("--system-prompt") + 1].startswith("你是助理") and "不要在回答中提及" in a[a.index("--system-prompt") + 1]
    assert sent["stdin"] == "問題"


def test_defaults_add_no_thinking_or_effort_flags(w):
    cmd, streaming, env = w.build_command(FAKE, {"model": "opus"}, {})
    assert "--effort" not in cmd and "--settings" not in cmd and env == {}
    assert cmd[cmd.index("--model") + 1] == "opus" and streaming


def test_per_job_model_effort_and_thinking(w):
    cmd, _, env = w.build_command(FAKE, {"model": "claude-opus-5", "effort": "high", "thinking": "off"}, {})
    assert cmd[cmd.index("--model") + 1] == "claude-opus-5"
    assert cmd[cmd.index("--effort") + 1] == "high"
    assert env == {"MAX_THINKING_TOKENS": "0"}
    cmd, _, _ = w.build_command(FAKE, {"alias": "sonnet"}, {})          # 0.1.0 以前的欄位名仍接受
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    for bad in ({"model": "gpt-4"}, {"effort": "ultra"}):
        with pytest.raises(ValueError):
            w.build_command(FAKE, bad, {})


def test_thinking_off_env_reaches_claude_and_note_for_models_that_cannot(w, monkeypatch, tmp_path):
    args_out = tmp_path / "args.json"
    monkeypatch.setenv("FAKE_CLAUDE_ARGS_OUT", str(args_out))
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "嗨" * 20)
    monkeypatch.setenv("FAKE_CLAUDE_MODEL", "claude-opus-5-5")
    worker = make_worker(w)
    worker.run_job({"job_id": "jt", "model": "opus", "thinking": "off", "prompt": "p"})
    sent = json.loads(args_out.read_text(encoding="utf-8"))
    assert sent["env_max_thinking"] == "0"
    result = next(b for p, b in w.calls if p.endswith("/result"))
    assert result["model"] == "claude-opus-5-5" and result["notes"] == ["thinking_off_not_applicable"]


def test_session_first_then_resume(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "嗨" * 50)
    sid = str(uuid.uuid4())
    cmd, _, _ = w.build_command(FAKE, {"session": sid}, {})
    assert cmd[cmd.index("--session-id") + 1] == sid
    worker = make_worker(w)
    worker.run_job({"job_id": "j2", "session": sid, "prompt": "p"})
    cmd, _, _ = w.build_command(FAKE, {"session": sid}, worker.sessions)
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
    worker.run_job({"job_id": "j5", "model": "gpt", "prompt": "p"})
    assert w.calls == [("/worker/jobs/j5/fail", {"code": "bad_job", "message": "不認得的模型 gpt"})]


def test_long_ascii_run_streams_instead_of_waiting_for_the_end(w, monkeypatch):
    """沒有空白的英數輸出(JSON、雜湊、長網址)以前會被整段扣住,到最後才一次送出(E2E 實踩)。"""
    text = "".join(f"{i:04d}." for i in range(60)) + " " + "x" * 100 + "@example.com 結束"
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", text)
    make_worker(w).run_job({"job_id": "j", "model": "haiku", "prompt": "q"})
    chunks = [b["text"] for p, b in w.calls if p.endswith("/chunk")]
    result = next(b for p, b in w.calls if p.endswith("/result"))
    assert len(chunks[0]) < 300 and len([c for c in chunks if len(c) >= 200]) > 1   # 途中就開始送
    assert all(result["text"].startswith(c) for c in chunks)                        # 仍是全文的前綴
    assert "@example.com" not in result["text"] and "x" * 36 + "[redacted]" in result["text"]


def test_killed_job_is_a_failure_not_a_truncated_success(w, monkeypatch):
    monkeypatch.setattr(w, "JOB_TIMEOUT_S", 1)
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "a" * 40)
    monkeypatch.setenv("FAKE_CLAUDE_DELAY_S", "0.4")
    make_worker(w).run_job({"job_id": "j", "model": "haiku", "prompt": "q"})
    assert not any(p.endswith("/result") for p, _ in w.calls)
    fail = next(b for p, b in w.calls if p.endswith("/fail"))
    assert fail["code"] == "worker_timeout"


def test_stream_without_result_event_is_incomplete(w, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_TEXT", "半截的回答半截的回答")
    monkeypatch.setenv("FAKE_CLAUDE_NO_RESULT", "1")
    make_worker(w).run_job({"job_id": "j", "model": "haiku", "prompt": "q"})
    assert not any(p.endswith("/result") for p, _ in w.calls)
    assert next(b for p, b in w.calls if p.endswith("/fail"))["code"] == "claude_incomplete"
