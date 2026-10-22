from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
import tomllib

from .errors import BridgeError
from .process import Child, check_cancel


def environment():
    env=dict(os.environ)
    for name in list(env):
        if name in {"ANTHROPIC_API_KEY","ANTHROPIC_AUTH_TOKEN","ANTHROPIC_BASE_URL","CLAUDE_CODE_OAUTH_TOKEN",
                    "OPENAI_API_KEY","OPENAI_BASE_URL","CODEX_API_KEY","CODEX_ACCESS_TOKEN","CLAUDECODE",
                    "CODEX_SESSION_ID","CODEX_THREAD_ID","CODEX_INTERNAL_ORIGINATOR_OVERRIDE","CODEX_APP_TOOLS_PIPE_PATH",
                    "CODEX_TOOL_CALL_ID"}:
            env.pop(name,None)
    env.update(NO_COLOR="1",CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",CLAUDE_CODE_SKIP_PROMPT_HISTORY="1")
    return env


def executable(provider,settings):
    found=settings.get(provider+"_path") or shutil.which(provider)
    if not found:
        raise BridgeError(503,"cli_missing","找不到 CLI，請在本機介面設定原生執行檔。")
    path=Path(found)
    if provider=="claude" and path.suffix.lower() in {".cmd",".bat",".ps1"}:
        path=path.parent/"node_modules/@anthropic-ai/claude-code/bin/claude.exe"
    elif provider=='codex' and path.suffix.lower() in {'.cmd','.bat','.ps1'}:
        packages=path.parent/'node_modules/@openai'
        candidates=[]
        for pattern in ('codex/vendor/**/codex.exe','codex/node_modules/@openai/codex-*/vendor/**/codex.exe','codex-*/vendor/**/codex.exe'):
            candidates.extend(p for p in packages.glob(pattern) if p.is_file())
        if candidates:path=sorted(candidates)[0]
    if not path.is_file() or path.suffix.lower() in {".cmd",".bat",".ps1"}:
        raise BridgeError(503,"cli_missing","請設定原生 CLI 執行檔；不透過 shell 啟動。")
    return str(path.resolve())


def status(provider,settings):
    try:
        cmd=[executable(provider,settings)]+(["auth","status"] if provider=="claude" else ["login","status"])
        proc=subprocess.run(cmd,capture_output=True,env=environment(),timeout=20,
                            creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        raw=(proc.stdout+proc.stderr).decode("utf-8","replace")
        if provider=="claude":
            data=json.loads(proc.stdout or b"{}")
            return {"provider":provider,"ready":bool(data.get("loggedIn")) and data.get("authMethod")=="claude.ai",
                    "method":data.get("authMethod"),"plan":data.get("subscriptionType")}
        return {"provider":provider,"ready":proc.returncode==0 and "ChatGPT" in raw,"method":"ChatGPT" if "ChatGPT" in raw else "其他／未登入"}
    except (OSError,ValueError,subprocess.SubprocessError,BridgeError):
        return {"provider":provider,"ready":False,"method":"CLI 不可用／未登入"}


def classify(text):
    for pattern,status,kind,message in [
        (r"(?i)rate.limit|usage.limit|hit your limit|429",429,"rate_limit_exceeded","訂閱額度或請求頻率受限，請稍後再試。"),
        (r"(?i)not logged|log in|unauthorized|authentication|401",503,"provider_authentication","CLI 訂閱登入失效，請自行在 CLI 重新登入。"),
        (r"(?i)model.*not.*exist|issue with.*model|unsupported.*model",400,"model_not_found","CLI 帳號無法使用指定模型。"),
        (r"(?i)connect|network|dns|failed to send|stream disconnected",502,"provider_unavailable","CLI 無法連接模型服務。")]:
        if re.search(pattern,text): return BridgeError(status,kind,message)
    return BridgeError(502,"provider_error","CLI 未正常完成；原始錯誤不寫入本機紀錄。")


def _token_count(value):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:
        raise BridgeError(502,'usage_unavailable','CLI 未回報有效 token 用量，無法換算牌價。')
    return value


def claude_usage(usage):
    usage=usage or {}
    ordinary=_token_count(usage.get('input_tokens'))
    output=_token_count(usage.get('output_tokens'))
    cached=_token_count(usage.get('cache_read_input_tokens',0))
    written=_token_count(usage.get('cache_creation_input_tokens',0))
    return {'prompt_tokens':ordinary+cached+written,'completion_tokens':output,
            'prompt_tokens_details':{'cached_tokens':cached,'cache_write_tokens':written,
                'cache_write_1h_tokens':_token_count((usage.get('cache_creation') or {}).get('ephemeral_1h_input_tokens',0))}}


def codex_usage(usage):
    usage=usage or {}
    return {'prompt_tokens':_token_count(usage.get('inputTokens')),
            'completion_tokens':_token_count(usage.get('outputTokens')),
            'prompt_tokens_details':{'cached_tokens':_token_count(usage.get('cachedInputTokens',0))},
            'completion_tokens_details':{'reasoning_tokens':_token_count(usage.get('reasoningOutputTokens',0))}}


def call_claude(spec,settings,cancel,cwd):
    if not status("claude",settings)["ready"]:
        raise BridgeError(503,"provider_authentication","Claude Code 尚未使用訂閱帳號登入。")
    command=[executable("claude",settings),"-p","--model",spec.model["native"],"--no-session-persistence",
             "--restricted","--tools","","--strict-mcp-config","--mcp-config",'{"mcpServers":{}}',
             "--setting-sources","","--output-format","stream-json","--verbose","--max-turns","1"]
    command += ["--system-prompt",spec.system or "You are a concise assistant. Never use tools. Follow the user instructions."]
    if spec.effort: command += ["--effort",spec.effort]
    if spec.schema: command += ["--json-schema",json.dumps(spec.schema)]
    parts=spec.messages[-1]["parts"]
    if any(p["type"]=="image_url" for p in parts):
        content=[]
        for part in parts:
            if part["type"]=="text": content.append(part)
            else:
                header,data=part["image_url"]["url"].split(",",1)
                content.append({"type":"image","source":{"type":"base64","media_type":header[5:].split(";")[0],"data":data}})
        command += ["--input-format","stream-json"]
        payload=json.dumps({"type":"user","message":{"role":"user","content":content}})+"\n"
    else: payload="\n".join(p["text"] for p in parts)
    child=Child(command,cwd,environment())
    try:
        raw=child.communicate(payload.encode(),cancel,settings.get("timeout_s"))
        try:
            events=[json.loads(line) for line in raw.splitlines() if line.strip()]
            result=next(e for e in reversed(events) if e.get("type")=="result")
        except (ValueError,StopIteration):
            raise BridgeError(502,"invalid_provider_response","CLI 回應不是合法 JSON。") from None
        if child.proc.returncode or result.get("is_error"):
            raise classify(str(result.get("result", "")))
        text=result.get("result") or ""
        if "structured_output" in result and result["structured_output"] is not None:
            text=json.dumps(result["structured_output"],ensure_ascii=False,separators=(",",":"))
        usage=result.get("usage") or {}
        return text,claude_usage(usage),"stop"
    finally: child.close()


def codex_command(settings):
    command=[executable("codex",settings),"app-server","--listen","stdio://"]
    config={"web_search":"disabled","analytics.enabled":False,"feedback.enabled":False,"notify":[],
            "agents.enabled":False,"project_doc_max_bytes":0}
    for name in ("hooks","memories","shell_tool","unified_exec","code_mode","apps","plugins","browser_use",
                 "browser_use_external","computer_use","image_generation","multi_agent","multi_agent_v2",
                 "view_image","in_app_browser","artifact","workspace_dependencies","sleep_tool","remote_plugin","skill_search","tool_suggest"):
        config["features."+name]=False
    path=Path(os.environ.get("CODEX_HOME") or Path.home()/".codex")/"config.toml"
    try:
        personal=tomllib.loads(path.read_text(encoding="utf-8"))
        for name in personal.get("mcp_servers",{}):
            if re.fullmatch(r"[A-Za-z0-9_-]+",name): config[f"mcp_servers.{name}.enabled"]=False
    except (OSError,ValueError): pass
    for key,value in config.items(): command += ["-c",key+"="+json.dumps(value,separators=(",",":"))]
    return command


def call_codex(spec,settings,cancel,cwd):
    if not status("codex",settings)["ready"]:
        raise BridgeError(503,"provider_authentication","Codex 尚未使用 ChatGPT 訂閱登入。")
    child=Child(codex_command(settings),cwd,environment())
    messages=queue.Queue(maxsize=4096); overflow=threading.Event()
    def reader():
        try:
            for line in child.proc.stdout:
                if len(line)>4_000_000: overflow.set(); break
                try: message=json.loads(line)
                except ValueError: continue
                try: messages.put_nowait(message)
                except queue.Full: overflow.set(); break
        finally:
            try: messages.put_nowait({"_eof":True})
            except queue.Full: pass
    def drain():
        while child.proc.stderr.read(65536): pass
    threading.Thread(target=reader,daemon=True).start()
    threading.Thread(target=drain,daemon=True).start()
    deadline=time.monotonic()+settings.get("timeout_s")
    next_id=0
    def send(method,params=None,notification=False):
        nonlocal next_id
        next_id+=1
        message={"method":method,"params":params or {}}
        if not notification: message["id"]=next_id
        child.proc.stdin.write((json.dumps(message)+"\n").encode()); child.proc.stdin.flush()
        return next_id
    def receive():
        while True:
            check_cancel(cancel,deadline)
            if overflow.is_set(): raise BridgeError(502,"output_too_large","CLI 事件佇列超過上限。")
            try:
                value=messages.get(timeout=.1)
            except queue.Empty: continue
            if value.get("_eof"): raise BridgeError(502,"provider_error","Codex 提前結束。")
            # No public request may drive a local tool or approval flow.
            if "method" in value and "id" in value:
                raise BridgeError(502,"tool_execution_blocked","此服務未開放本機工具或權限問答。")
            if value.get("method")=="item/started":
                kind=value.get("params",{}).get("item",{}).get("type")
                if kind not in {"userMessage","agentMessage","reasoning","plan"}:
                    raise BridgeError(502,"tool_execution_blocked","此服務未開放本機工具。")
            return value
    def response(rid):
        while True:
            m=receive()
            if m.get("id")==rid:
                if "error" in m: raise classify(str(m["error"].get("message","")))
                return m.get("result",{})
    try:
        response(send("initialize",{"clientInfo":{"name":"aigo_llm_bridge","version":"0.2.0"},"capabilities":{"experimentalApi":True}}))
        send("initialized",notification=True)
        start=response(send("thread/start",{"cwd":cwd,"ephemeral":True,"model":spec.model["native"],
            "approvalPolicy":"never","sandbox":"read-only",
            "baseInstructions":"You are an LLM inference assistant. Never use tools, access files, execute commands, or create sessions.\n"+spec.system,
            "developerInstructions":"Only return the requested answer. No tools are available.",
            "config":{"project_doc_max_bytes":0},"dynamicTools":[]}))
        if start.get("model")!=spec.model["native"]:
            raise BridgeError(502,"model_mismatch","CLI 使用的模型與請求不同。")
        if not start.get("thread",{}).get("ephemeral") or start["thread"].get("path"):
            raise BridgeError(503,"session_isolation","CLI 未建立記憶體 thread，已停止執行。")
        tid=start["thread"]["id"]
        if len(spec.messages)>1:
            history=[]
            for msg in spec.messages[:-1]:
                content=[]
                for part in msg["parts"]:
                    if part["type"]=="text": content.append({"type":"output_text" if msg["role"]=="assistant" else "input_text","text":part["text"]})
                    else: content.append({"type":"input_image","image_url":part["image_url"]["url"]})
                history.append({"type":"message","role":msg["role"],"content":content})
            response(send("thread/inject_items",{"threadId":tid,"items":history}))
        inputs=[]
        for part in spec.messages[-1]["parts"]:
            if part["type"]=="text": inputs.append({"type":"text","text":part["text"]})
            else:
                entry={"type":"image","url":part["image_url"]["url"]}
                if part["image_url"]["detail"]!="auto": entry["detail"]=part["image_url"]["detail"]
                inputs.append(entry)
        params={"threadId":tid,"input":inputs}
        if spec.effort: params["effort"]=spec.effort
        if spec.schema: params["outputSchema"]=spec.schema
        rid=send("turn/start",params)
        chunks=[]; size=0; usage={}; final=None
        while True:
            m=receive(); method=m.get("method"); p=m.get("params",{})
            if m.get("id")==rid and "error" in m: raise classify(str(m["error"].get("message","")))
            if method=="item/agentMessage/delta":
                delta=p.get("delta",""); size+=len(delta)
                if size>1_000_000: raise BridgeError(502,"output_too_large","回應超過服務上限。")
                chunks.append(delta)
            if method=="thread/tokenUsage/updated": usage=p.get("tokenUsage",{}).get("total") or {}
            if method=="turn/completed":
                final=p.get("turn",{})
                break
        if not final or final.get("status")!="completed":
            raise classify(str((final or {}).get("error",{})))
        return "".join(chunks),codex_usage(usage),"stop"
    except (BrokenPipeError,OSError):
        raise BridgeError(502,"provider_unavailable","CLI 通道中斷。") from None
    finally: child.close()


def infer(spec,settings,cancel):
    # Only empty working directories touch disk. Request content stays in pipes/RAM.
    with tempfile.TemporaryDirectory(prefix="aigo-inference-") as cwd:
        return (call_claude if spec.model["provider"]=="claude" else call_codex)(spec,settings,cancel,cwd)
