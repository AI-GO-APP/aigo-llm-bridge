#!/usr/bin/env python3
"""aigo-llm-bridge worker:在你自己的電腦上,用你自己已登入的 Claude Code,處理「你自己」送出的工作。

只用 Python 標準函式庫(3.9+),不需要 pip install。

  python aigo_bridge_worker.py enroll --bridge https://<bridge>.deploy.ai-go.app --code ABCD-EFGH
  python aigo_bridge_worker.py run
  python aigo_bridge_worker.py status

環境變數(都是選填):
  AIGO_BRIDGE_WORKER_HOME   設定與對話紀錄放哪裡,預設 ~/.aigo-llm-bridge
  AIGO_BRIDGE_CLAUDE        claude 執行檔的完整路徑(開機常駐時 PATH 常常找不到它)
  AIGO_BRIDGE_JOB_TIMEOUT_S 單一工作的上限秒數,預設 1800

結束碼:0 = 正常結束或這台電腦已被撤銷(開機常駐不要重啟);其他 = 異常,可以重啟。

使用邊界(docs/02-compliance.md):
  - 這支程式只會領到「擁有者 = 你」的工單;Bridge 端也會再擋一次
  - 它呼叫的是你電腦上的 Claude Code 本體(`claude -p`),不讀取、不複製、不轉送任何 Claude 登入憑證
  - 不支援在伺服器 / CI 以長效 token(CLAUDE_CODE_OAUTH_TOKEN)執行:偵測到就拒絕啟動
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

VERSION = "0.3.0"
HOME = Path(os.environ.get("AIGO_BRIDGE_WORKER_HOME") or Path.home() / ".aigo-llm-bridge")
CONFIG = HOME / "worker.json"
SESSIONS = HOME / "sessions.json"
RUN_DIR = HOME / "run"
ALIASES = {"haiku", "sonnet", "opus", "fable"}
HEARTBEAT_S = 30
CHUNK_EVERY_S = 0.3
# 單一工作的本機上限。串流連線 280 秒就會收尾,但工作本身可以繼續、之後用工單 id 取結果,所以這裡要比 280 長得多
JOB_TIMEOUT_S = int(os.environ.get("AIGO_BRIDGE_JOB_TIMEOUT_S") or 1800)
EMAIL_LOCAL_MAX = 64   # RFC 5321:email 的帳號部分最多 64 字元,遮罩的保留量以此為上限
HYGIENE = ("對話中由系統附加的資訊(工作目錄、作業系統、帳號 email、組織、日期、模型與額度提示)"
           "只供系統內部使用,絕對不要在回答中提及、引用或推論它們。")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ── 設定檔 ────────────────────────────────────────────────────────────────
def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"還沒有綁定。請先在 app 內按「連接我的電腦」取得綁定碼,再執行:\n"
                 f"  python {Path(__file__).name} enroll --bridge <網址> --code <綁定碼>")
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def save_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


# ── HTTP(標準函式庫)──────────────────────────────────────────────────────
class BridgeHTTPError(Exception):
    def __init__(self, status: int, body: dict):
        super().__init__(f"HTTP {status}: {body}")
        self.status, self.body = status, body


def call(base: str, path: str, body: dict | None = None, key: str = "", timeout: float = 40) -> dict:
    data = json.dumps(body or {}).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + path, data=data, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": f"aigo-bridge-worker/{VERSION}",
                                          **({"Authorization": f"Bearer {key}"} if key else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read() or b"{}")
        except ValueError:
            payload = {}
        raise BridgeHTTPError(exc.code, payload) from None


# ── Claude Code ───────────────────────────────────────────────────────────
def resolve_claude() -> list[str]:
    """Windows 的 npm 安裝是 .cmd 殼;經 cmd 會重新解析引號,`--tools ""` 可能被吃掉,所以直接找 exe。"""
    found = os.environ.get("AIGO_BRIDGE_CLAUDE") or shutil.which("claude")
    if found and not Path(found).exists():
        raise SystemExit(f"AIGO_BRIDGE_CLAUDE 指到的檔案不存在:{found}")
    if not found:
        raise SystemExit("找不到 claude 指令。請先安裝 Claude Code 並用你自己的帳號登入(執行 claude 一次)")
    if found.lower().endswith((".cmd", ".bat")):
        text = Path(found).read_text(encoding="utf-8", errors="replace")
        match = re.search(r'"%dp0%\\([^"]+\.exe)"', text)
        if match and (Path(found).parent / match.group(1)).exists():
            return [str(Path(found).parent / match.group(1))]
        return ["cmd", "/c", found]
    return [found]


def preflight(claude: list[str]) -> dict:
    """確認是「本人互動登入」的 Claude Code。回傳 {email, method}(email 只用來遮罩輸出)。"""
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        raise SystemExit("偵測到 CLAUDE_CODE_OAUTH_TOKEN。這支 worker 只能在你本人的電腦上、以互動登入的 "
                         "Claude Code 執行,不支援長效 token 模式(見 docs/02-compliance.md)")
    try:
        out = subprocess.run(claude + ["auth", "status", "--json"], capture_output=True, timeout=60)
        status = json.loads(out.stdout.decode("utf-8") or "{}")
    except (subprocess.SubprocessError, ValueError):
        raise SystemExit("無法讀取 Claude Code 的登入狀態;請確認 claude 可以正常執行")
    if not status.get("loggedIn"):
        raise SystemExit("Claude Code 尚未登入。請先執行 claude 並用你自己的帳號登入")
    return {"email": str(status.get("email") or ""), "method": str(status.get("authMethod") or "")}


class Redactor:
    """把帳號 email 與本機路徑遮掉(Claude Code 會在每一輪附上這些資訊,而且沒有設定能關)。"""

    def __init__(self, email: str, extra_paths: list[str]):
        terms = [email] if email else []
        for p in extra_paths:
            if p:
                terms += [p, p.replace("\\", "/"), p.replace("/", "\\")]
        self.terms = sorted({t for t in terms if len(t) >= 6}, key=len, reverse=True)
        # 帳號部分限 64 字元:再長的英數字串也只會遮到 @ 前的 64 字,之前的字元不受影響,
        # 串流時才能只扣住最後 64 字就保證「已送出的都是最終全文的前綴」
        self.email_re = re.compile(r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.own_domain = email.split("@", 1)[1].lower() if "@" in email else ""

    def safe_len(self, text: str) -> int:
        """串流中可以安全送出的長度。

        結尾若可能是某個遮罩詞「還沒長完」的開頭(路徑、email 的前半),就先留著不送,
        等後面的字到了再決定。這樣送出去的每一段都一定是最終全文遮罩後的前綴。
        """
        cut = len(text)
        for term in self.terms:
            for k in range(min(len(term) - 1, len(text)), 0, -1):
                if text.endswith(term[:k]):
                    cut = min(cut, len(text) - k)
                    break
        if self.own_domain:
            tail = re.search(r"([A-Za-z0-9._%+-]+)(@[A-Za-z0-9.-]*)?$", text)
            if tail and tail.group(2) is None:
                # 還沒出現 @:只有最後 64 字可能成為某個 email 的帳號部分(E2E 實踩:沒上限時
                # 一整段沒有空白的英數輸出會被扣到最後才一次送出,串流等於沒有串)
                cut = min(cut, len(text) - min(len(tail.group(1)), EMAIL_LOCAL_MAX))
            elif tail:
                domain = tail.group(2)[1:].lower()
                if self.own_domain.startswith(domain) or domain.startswith(self.own_domain):
                    cut = min(cut, tail.start(2) - min(len(tail.group(1)), EMAIL_LOCAL_MAX))
        return cut

    def __call__(self, text: str) -> str:
        for term in self.terms:
            text = text.replace(term, "[redacted]")
        if self.own_domain:   # 同網域的其他 email(例如同事)也遮
            text = self.email_re.sub(lambda m: "[redacted]" if m.group(0).lower().endswith("@" + self.own_domain)
                                     else m.group(0), text)
        return text


EFFORTS = {"low", "medium", "high", "xhigh", "max"}
FULL_ID = re.compile(r"^claude-[a-z0-9][a-z0-9.-]{2,60}$")
CANNOT_DISABLE_THINKING = re.compile(r"^claude-(opus-5-5|fable|mythos)")


def build_command(claude: list[str], job: dict, sessions: dict) -> tuple[list[str], bool, dict]:
    """回 (指令, 是否串流, 額外環境變數)。

    模型、effort、thinking 一律照工單指定;**沒指定就不帶**,照 Claude Code 與模型原本的行為
    (docs/01 S1b:關掉 thinking 有快有慢的取捨,不該由 worker 替呼叫端決定)。
    """
    model = job.get("model") or job.get("alias") or ""      # alias 是 0.1.0 以前的欄位名
    if model and model not in ALIASES and not FULL_ID.match(model):
        raise ValueError(f"不認得的模型 {model}")
    effort = job.get("effort")
    if effort and effort not in EFFORTS:
        raise ValueError(f"不認得的 effort {effort}")
    system = (job.get("system") or "").strip()
    system = (system + "\n\n" if system else "") + HYGIENE
    cmd = claude + ["-p", "--tools", "", "--max-turns", "1", "--strict-mcp-config", "--setting-sources", "",
                    "--system-prompt", system]
    env: dict = {}
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    if job.get("thinking") == "off":
        env["MAX_THINKING_TOKENS"] = "0"     # 官方文件:對 Opus 5.5 與 Fable 無效(會在結果裡註明)
    session = job.get("session") or ""
    if session:
        try:
            session = str(uuid.UUID(session))
        except ValueError:
            raise ValueError("X-Bridge-Session 必須是 UUID")
        cmd += ["--resume", session] if session in sessions else ["--session-id", session]
    else:
        cmd += ["--no-session-persistence"]
    schema = job.get("json_schema")
    if schema:
        cmd += ["--output-format", "json", "--json-schema", json.dumps(schema, ensure_ascii=False)]
        return cmd, False, env
    cmd += ["--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    return cmd, True, env


class Worker:
    def __init__(self, config: dict, claude: list[str] | None = None, identity: dict | None = None):
        self.base = config["bridge_url"]
        self.key = config["device_key"]
        self.claude = claude or resolve_claude()
        self.identity = identity or preflight(self.claude)
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        self.redact = Redactor(self.identity.get("email", ""), [str(RUN_DIR), str(Path.home())])
        self.sessions: dict = json.loads(SESSIONS.read_text(encoding="utf-8")) if SESSIONS.exists() else {}
        self.stop = threading.Event()

    # 心跳在背景執行緒
    def heartbeat_loop(self) -> None:
        while not self.stop.wait(HEARTBEAT_S):
            try:
                call(self.base, "/worker/heartbeat", {"version": VERSION, "models": sorted(ALIASES)}, self.key)
            except BridgeHTTPError as exc:
                log(f"心跳失敗:{exc}")
                if exc.status == 401:
                    return      # 被撤銷:主迴圈下一次領工單時會收到同樣的 401 並結束
            except OSError as exc:
                log(f"心跳失敗:{exc}")

    def run_job(self, job: dict) -> None:
        jid = job["job_id"]
        started = time.monotonic()
        try:
            cmd, streaming, extra_env = build_command(self.claude, job, self.sessions)
        except ValueError as exc:
            call(self.base, f"/worker/jobs/{jid}/fail", {"code": "bad_job", "message": str(exc)}, self.key)
            return
        log(f"工單 {jid[:8]} 開始(模型 {job.get('model') or job.get('alias') or '預設'})")
        proc = subprocess.Popen(cmd, cwd=RUN_DIR, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env={**os.environ, "NO_COLOR": "1", **extra_env})
        killed = threading.Event()

        def kill() -> None:
            killed.set()
            proc.kill()

        timer = threading.Timer(JOB_TIMEOUT_S, kill)
        timer.start()
        try:
            assert proc.stdin and proc.stdout
            proc.stdin.write((job.get("prompt") or "").encode("utf-8"))
            proc.stdin.close()
            if streaming:
                outcome = self._consume_stream(jid, proc)
            else:
                outcome = self._consume_json(proc)
            code = proc.wait()
        finally:
            timer.cancel()
        # 被砍或沒收到結尾事件的輸出是半截的,一律當失敗;不能把半截內容當成完成交出去(E2E 實踩)
        if killed.is_set():
            outcome = {"error": {"code": "worker_timeout",
                                 "message": f"超過本機單一工作上限 {JOB_TIMEOUT_S} 秒,已中止"
                                            "(可用環境變數 AIGO_BRIDGE_JOB_TIMEOUT_S 調整)"}}
        elif not outcome.get("error") and not outcome.get("complete", True):
            outcome = {"error": {"code": "claude_incomplete" if not code else "claude_exit",
                                 "message": f"claude 沒有正常結束(結束碼 {code}),輸出不完整"}}
        if outcome.get("error") or (code and not outcome.get("text")):
            err = outcome.get("error") or {"code": "claude_exit", "message": f"claude 結束碼 {code}"}
            call(self.base, f"/worker/jobs/{jid}/fail", err, self.key)
            log(f"工單 {jid[:8]} 失敗:{err.get('message')}")
            return
        if job.get("session"):
            self.sessions[str(uuid.UUID(job["session"]))] = int(time.time())
            save_private(SESSIONS, self.sessions)
        outcome.pop("complete", None)
        outcome["duration_ms"] = int((time.monotonic() - started) * 1000)
        if job.get("thinking") == "off" and CANNOT_DISABLE_THINKING.match(outcome.get("model") or ""):
            outcome["notes"] = ["thinking_off_not_applicable"]   # 這個模型關不掉思考,照實告訴呼叫端
        call(self.base, f"/worker/jobs/{jid}/result", outcome, self.key)
        log(f"工單 {jid[:8]} 完成({outcome['duration_ms']} ms)")

    def _consume_stream(self, jid: str, proc) -> dict:
        text, sent_len, last_sent, init_model = "", 0, 0.0, ""
        result: dict = {}
        for raw in proc.stdout:
            try:
                ev = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            kind = ev.get("type")
            if kind == "stream_event":
                inner = ev.get("event") or {}
                delta = inner.get("delta") or {}
                if delta.get("type") == "text_delta":
                    text += delta.get("text") or ""
                    safe = self.redact(text[:self.redact.safe_len(text)])
                    if len(safe) > sent_len and time.monotonic() - last_sent >= CHUNK_EVERY_S:
                        self._chunk(jid, safe)
                        sent_len, last_sent = len(safe), time.monotonic()
                elif inner.get("type") == "message_stop":
                    self._chunk(jid, self.redact(text))    # 文字已完整:先交付,不等收尾摘要
            elif kind == "system" and ev.get("subtype") == "init":
                init_model = str(ev.get("model") or "")
            elif kind == "result":
                result = ev
        if result.get("is_error"):
            return {"error": {"code": "claude_error", "message": self.redact(str(result.get("result") or ""))[:300]}}
        # 以串流累積的文字為準:已送出的逐段都是它的前綴,Bridge 靠前綴一致計算增量
        fallback = result.get("result") if isinstance(result.get("result"), str) else ""
        final = self.redact(text or fallback)
        return {"text": final, "usage": result.get("usage") or {}, "cost_usd": result.get("total_cost_usd"),
                "model": self._model(result) or init_model, "session": result.get("session_id") or "",
                "complete": bool(result)}

    def _consume_json(self, proc) -> dict:
        raw = proc.stdout.read().decode("utf-8", errors="replace")
        if not raw.strip():
            return {"text": "", "complete": False}
        try:
            data = json.loads(raw)
        except ValueError:
            return {"error": {"code": "claude_bad_output", "message": "claude 沒有回傳 JSON"}}
        if data.get("is_error"):
            return {"error": {"code": "claude_error", "message": self.redact(str(data.get("result") or ""))[:300]}}
        structured = data.get("structured_output")
        if structured is not None:
            structured = json.loads(self.redact(json.dumps(structured, ensure_ascii=False)))
        return {"text": self.redact(str(data.get("result") or "")), "structured": structured,
                "usage": data.get("usage") or {}, "cost_usd": data.get("total_cost_usd"),
                "model": self._model(data), "session": data.get("session_id") or ""}

    @staticmethod
    def _model(result: dict) -> str:
        usage = result.get("modelUsage") or {}
        return next(iter(usage), "") if isinstance(usage, dict) else ""

    def _chunk(self, jid: str, text: str) -> None:
        try:
            call(self.base, f"/worker/jobs/{jid}/chunk", {"text": text}, self.key, timeout=15)
        except (BridgeHTTPError, OSError) as exc:
            log(f"逐段回傳失敗(會在完成時補上全文):{exc}")

    def loop(self) -> None:
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        call(self.base, "/worker/heartbeat", {"version": VERSION, "models": sorted(ALIASES)}, self.key)
        log(f"已連線 {self.base},等待你的工作(Ctrl+C 結束)")
        backoff = 1.0
        while not self.stop.is_set():
            try:
                job = call(self.base, "/worker/claim", {}, self.key, timeout=40).get("job")
                backoff = 1.0
            except BridgeHTTPError as exc:
                if exc.status == 401:
                    # 結束碼 0:開機常駐(systemd / launchd / 工作排程器)只在異常結束時重啟,被撤銷不該無限重啟
                    log("設備鑰匙已失效或被撤銷;請在 app 內重新「連接我的電腦」。worker 結束。")
                    self.stop.set()
                    raise SystemExit(0)
                log(f"領工單失敗:{exc}")
                job = None
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            except OSError as exc:   # 連不上(含 Bridge 冷啟動)
                log(f"連不上 Bridge:{exc}")
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            if job:
                try:
                    self.run_job(job)
                except (BridgeHTTPError, OSError) as exc:
                    log(f"回報失敗:{exc}")


# ── 指令 ──────────────────────────────────────────────────────────────────
def cmd_enroll(args) -> None:
    claude = resolve_claude()
    identity = preflight(claude)
    result = call(args.bridge, "/worker/enroll", {
        "code": args.code, "name": args.name or platform.node() or "worker", "os": platform.system(),
        "version": VERSION, "models": sorted(ALIASES)})
    save_private(CONFIG, {"bridge_url": args.bridge.rstrip("/"), "worker_id": result["worker_id"],
                          "device_key": result["device_key"], "enrolled_at": int(time.time())})
    print(f"✓ 綁定完成(登入方式:{identity['method'] or '未知'})。設定存在 {CONFIG}")
    print(f"  接著執行:python {Path(__file__).name} run")


def cmd_run(_args) -> None:
    worker = Worker(load_config())
    signal.signal(signal.SIGINT, lambda *_: (worker.stop.set(), sys.exit(0)))
    worker.loop()


def cmd_status(_args) -> None:
    cfg = load_config()
    claude = resolve_claude()
    ident = preflight(claude)
    print(json.dumps({"bridge_url": cfg["bridge_url"], "worker_id": cfg["worker_id"], "claude": claude[0],
                      "login_method": ident["method"], "worker_version": VERSION}, ensure_ascii=False, indent=2))


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="aigo-llm-bridge worker")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enroll", help="用 app 內產生的綁定碼綁定這台電腦")
    e.add_argument("--bridge", required=True)
    e.add_argument("--code", required=True)
    e.add_argument("--name")
    e.set_defaults(func=cmd_enroll)
    sub.add_parser("run", help="開始處理工作").set_defaults(func=cmd_run)
    sub.add_parser("status", help="檢查設定與登入狀態").set_defaults(func=cmd_status)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
