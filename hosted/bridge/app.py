"""Bridge 的 HTTP 介面。端點與規則見 docs/09-api-reference.md。"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from . import config as config_mod
from . import routing
from .auth import Caller, authenticate, mint_session
from .errors import BridgeError
from .local import AsyncAccepted, LocalService, _completion, usage_from_worker
from .providers.base import CallContext
from .store import AigoStore, MemoryStore, Store, new_key, now

BOOT = time.time()
STREAM_CAP_S = 280.0   # Hosted 單一請求上限 300 秒(docs/01 S5),留 20 秒收尾
INSTANCE = uuid.uuid4().hex[:8]


def _has_output(chunk: dict) -> bool:
    """這一段有沒有真的內容(文字、工具呼叫或結束訊號);只有 role 的開頭段不算。"""
    for choice in chunk.get("choices") or []:
        delta = choice.get("delta") or {}
        if delta.get("content") or delta.get("tool_calls") or choice.get("finish_reason"):
            return True
    return False


def _sse(obj) -> bytes:
    return f"data: {obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)}\n\n".encode()


def create_app(settings: config_mod.Settings | None = None, store: Store | None = None,
               providers: dict | None = None) -> FastAPI:
    s = settings or config_mod.load()
    if store is None:
        store = MemoryStore() if s.store_backend == "memory" else AigoStore(s.aigo_api_url, s.aigo_api_token,
                                                                           s.table_prefix)
    local = LocalService(s, store)
    prefs = routing.Preferences(store)
    provider_cache: dict = dict(providers or {})
    background: set[asyncio.Task] = set()

    app = FastAPI(title="aigo-llm-bridge", version=s.version, docs_url=None, redoc_url=None)
    # Custom App 執行頁的 CSP 允許 *.ai-go.app;錯誤回應也要帶 CORS 標頭,瀏覽器才讀得到錯誤內容
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "PUT", "OPTIONS"],
                       allow_headers=["Authorization", "Content-Type", "X-Bridge-User", "X-Bridge-Session", "X-Bridge-Wait",
                                      "X-Bridge-Async", "X-Bridge-Source", "X-Bridge-Timestamp",
                                      "X-Bridge-Signature"],
                       expose_headers=["X-Bridge-Dropped", "X-Bridge-Served-By", "X-Bridge-Job", "X-Bridge-Priority",
                                      "X-Bridge-Fallback", "Retry-After"])
    app.state.settings, app.state.store, app.state.local = s, store, local

    @app.exception_handler(BridgeError)
    async def _bridge_error(_request: Request, exc: BridgeError):
        return exc.response()

    # ── 小工具 ────────────────────────────────────────────────────────────
    async def caller_of(request: Request, body: bytes) -> Caller:
        return authenticate(s, request.headers, body)

    def provider_for(name: str):
        if name not in provider_cache:
            if name == "anthropic":
                from .providers.anthropic import AnthropicProvider
                provider_cache[name] = AnthropicProvider(s.anthropic_api_key, fallbacks=s.anthropic_fallbacks)
            elif name == "openrouter":
                from .providers.openrouter import OpenRouterProvider
                provider_cache[name] = OpenRouterProvider(s.openrouter_api_key, base_url=s.openrouter_base_url)
        return provider_cache[name]

    def route_model(model: str) -> tuple[str, str]:
        """回 (後端, 傳給後端的 model)。規則見 docs/09 §2。

        相容既有 OpenRouter 呼叫端:它們的 model 長得像 `anthropic/claude-haiku-4.5`、`openai/gpt-5.4-mini`。
        - `anthropic/…` 有 Anthropic 金鑰就直連,並把 OpenRouter 的點號寫法換成 API 的連字號寫法
          (claude-haiku-4.5 → claude-haiku-4-5);沒有 Anthropic 金鑰就原樣交給 OpenRouter
        - 其他 `<vendor>/<model>` 有 OpenRouter 金鑰就原樣交給 OpenRouter
        """
        model = (model or "").strip() or s.default_model
        if not model:
            raise BridgeError(400, "model_required", "model 必填(或設定 BRIDGE_DEFAULT_MODEL)")
        prefix, _, rest = model.partition("/")
        if prefix == "local":
            return "local", model
        if prefix == "openrouter" and rest:
            return "openrouter", rest
        if prefix == "anthropic" and rest:
            if s.anthropic_api_key or "anthropic" in provider_cache:
                return "anthropic", rest.replace(".", "-")
            if s.openrouter_api_key or "openrouter" in provider_cache:
                return "openrouter", model
            raise BridgeError(503, "provider_not_configured", "Bridge 沒有設定 ANTHROPIC_API_KEY 或 OPENROUTER_API_KEY")
        if not rest and model.startswith("claude-"):
            return route_model("anthropic/" + model)
        if rest and (s.openrouter_api_key or "openrouter" in provider_cache):
            return "openrouter", model
        if not rest and s.default_model and model != s.default_model:
            raise BridgeError(400, "unknown_model", f"不認得的 model「{model}」;要用預設模型請不要帶 model")
        raise BridgeError(400, "unknown_provider", "model 要以 anthropic/、openrouter/ 或 local/ 開頭")

    def model_label(model: str) -> str:
        return (model or "").strip() or s.default_model

    async def record_usage(ctx: CallContext, provider: str, status: str, http_status: int, started: float,
                           stream: bool) -> None:
        usage = ctx.usage or {}
        try:
            await store.insert("usage", {
                "key": ctx.job_id or new_key(), "source": ctx.source, "owner": ctx.user, "provider": provider,
                "model": ctx.model_label, "served_by": ctx.served_by, "status": status, "http_status": http_status,
                "stream": stream, "prompt_tokens": int(usage.get("prompt_tokens") or 0),
                "completion_tokens": int(usage.get("completion_tokens") or 0),
                "cost_usd": float(usage.get("cost") or usage.get("cost_usd") or 0),
                "duration_ms": int((time.monotonic() - started) * 1000), "created_ts": now()})
        except BridgeError:
            pass   # 用量帳寫不進去不影響回應

    def headers_for(ctx: CallContext) -> dict[str, str]:
        out = {}
        if ctx.dropped:
            out["X-Bridge-Dropped"] = ",".join(ctx.dropped)
        if ctx.served_by:
            out["X-Bridge-Served-By"] = ctx.served_by
        if ctx.job_id:
            out["X-Bridge-Job"] = ctx.job_id
        if ctx.priority:
            out["X-Bridge-Priority"] = ctx.priority
        if ctx.fallback:
            out["X-Bridge-Fallback"] = f"{ctx.fallback['from']}:{ctx.fallback['reason']}"
        return out

    async def finish_job(job: dict, backend: str, ctx: CallContext, started: float, task: asyncio.Task) -> None:
        """背景把一個已經在跑的呼叫做完,結果寫回工單(非同步模式、同步逾時轉工單都走這裡)。"""
        try:
            result = await task
            await store.update("jobs", job, {"status": "done", "done_ts": now(),
                                             "result_json": {"completion": result}})
            await record_usage(ctx, backend, "ok", 200, started, False)
        except BridgeError as exc:
            await store.update("jobs", job, {"status": "failed", "done_ts": now(),
                                             "error_json": exc.body()["error"]})
            await record_usage(ctx, backend, "error", exc.status, started, False)

    def parse_wait(request: Request) -> float:
        raw = request.headers.get("x-bridge-wait", "").strip()
        if not raw:
            return 0.0
        try:
            value = float(raw)
        except ValueError:
            raise BridgeError(400, "bad_wait", "X-Bridge-Wait 要是秒數(1–280)") from None
        return max(1.0, min(value, STREAM_CAP_S))

    def spawn(coro) -> None:
        task = asyncio.create_task(coro)
        background.add(task)
        task.add_done_callback(background.discard)

    # ── 公開端點 ──────────────────────────────────────────────────────────
    @app.get("/healthz")
    async def healthz():
        return {"ok": True, "version": s.version, "instance": INSTANCE, "uptime_s": round(time.time() - BOOT, 1),
                "store": s.store_backend,
                "providers": {"anthropic": bool(s.anthropic_api_key), "openrouter": bool(s.openrouter_api_key),
                              "local": True},
                "sources": len(s.source_keys)}

    @app.get("/v1/models")
    async def models(request: Request):
        await caller_of(request, b"")
        data = [{"id": "auto", "object": "model", "owned_by": "bridge"},
                {"id": "local/self", "object": "model", "owned_by": "local"}]
        if s.anthropic_api_key:
            data += [{"id": f"anthropic/{m}", "object": "model", "owned_by": "anthropic"}
                     for m in ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5")]
        return {"object": "list", "data": data}

    @app.post("/bridge/session")
    async def session(request: Request):
        body = await request.body()
        caller = await caller_of(request, body)
        if caller.kind == "session":
            raise BridgeError(403, "forbidden", "session token 不能再換發 token")
        data = json.loads(body or b"{}")
        user = str(data.get("user") or caller.user or "").strip()
        if not user:
            raise BridgeError(400, "user_required", "user 必填(平台使用者 id)")
        token, exp = mint_session(s, caller.source, user, int(data.get("ttl") or 3600))
        return {"token": token, "exp": exp}

    @app.post("/bridge/enrollments")
    async def enrollments(request: Request):
        body = await request.body()
        caller = await caller_of(request, body)
        if caller.kind == "session":
            raise BridgeError(403, "forbidden", "綁定碼要由 app 的伺服器端(Server Action)代表使用者發起")
        return await local.create_enrollment(caller.source, caller.user)

    @app.get("/bridge/workers")
    async def my_workers(request: Request):
        caller = await caller_of(request, b"")
        if not caller.user:
            raise BridgeError(400, "user_required", "需要使用者身分")
        return {"workers": await local.list_workers(caller.user)}

    async def prefs_view(caller: Caller) -> dict:
        row = await prefs.get(caller.source, caller.user)
        worker = await local.online_worker(caller.user)
        return {
            "priority": (row or {}).get("priority") or None,
            "updated_at": int((row or {}).get("updated_ts") or 0) or None,
            "choices": [
                {"id": "local", "label": routing.LABELS["local"], "model": s.auto_local_model,
                 "available": bool(worker)},
                {"id": "cloud", "label": routing.LABELS["cloud"], "model": s.auto_cloud_model or None,
                 "available": cloud_ready(s.auto_cloud_model)},
            ],
        }

    @app.get("/bridge/preferences")
    async def get_preferences(request: Request):
        caller = await caller_of(request, b"")
        if not caller.user:
            raise BridgeError(400, "user_required", "需要使用者身分")
        return await prefs_view(caller)

    @app.api_route("/bridge/preferences", methods=["PUT", "POST"])
    async def set_preferences(request: Request):
        raw = await request.body()
        caller = await caller_of(request, raw)
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise BridgeError(400, "bad_json", "請求內容不是合法 JSON") from None
        await prefs.set(caller.source, caller.user, str(data.get("priority") or ""))
        return await prefs_view(caller)

    @app.post("/bridge/workers/{worker_id}/revoke")
    async def revoke(worker_id: str, request: Request):
        caller = await caller_of(request, await request.body())
        if not caller.user:
            raise BridgeError(400, "user_required", "需要使用者身分")
        await local.revoke_worker(caller.user, worker_id)
        return {"ok": True}

    # ── 相容端點 ──────────────────────────────────────────────────────────
    def new_ctx(caller: Caller, request: Request, label: str) -> CallContext:
        return CallContext(source=caller.source, user=caller.user, model_label=label,
                           session=request.headers.get("x-bridge-session", "").strip(),
                           wait_s=parse_wait(request))

    async def sync_once(backend: str, model: str, req: dict, ctx: CallContext, started: float) -> dict:
        """一個後端的同步呼叫。等太久會丟 AsyncAccepted(轉工單、回 202)。"""
        if backend == "local":
            return await local.complete(req, ctx)
        # 等到呼叫端要求的秒數;還沒好就轉成工單在背景跑完,回 202 讓它之後查
        task = asyncio.create_task(provider_for(backend).complete(req, model, ctx))
        done, _ = await asyncio.wait({task}, timeout=ctx.wait_s or s.sync_timeout_s)
        if not done:
            job = await local.create_job(ctx, req, provider=backend)
            spawn(finish_job(job, backend, ctx, started, task))
            raise AsyncAccepted(job["key"])
        return task.result()

    def open_stream(backend: str, model: str, req: dict, ctx: CallContext) -> AsyncIterator[dict]:
        return local.stream(req, ctx) if backend == "local" else provider_for(backend).stream(req, model, ctx)

    def meta_of(ctx: CallContext) -> dict:
        meta = {"served_by": ctx.served_by, "dropped": list(ctx.dropped)}
        if ctx.priority:
            meta["priority"] = ctx.priority
            meta["fallback"] = ctx.fallback or None
        return meta

    def sync_response(result: dict, ctx: CallContext) -> JSONResponse:
        # 標頭之外也放進本體:Custom App 經 egress 的 ctx.http.call 拿不到回應標頭(E2E 實測)
        return JSONResponse({**result, "x_bridge": meta_of(ctx)}, headers=headers_for(ctx))

    def accepted(job_key: str) -> JSONResponse:
        return JSONResponse({"id": job_key, "status": "running"}, status_code=202, headers={"X-Bridge-Job": job_key})

    def stream_response(gen: AsyncIterator[dict], head: list[dict], ctx: CallContext, backend: str,
                        started: float) -> StreamingResponse:
        async def body():
            # Hosted 單一請求 300 秒一到就直接斷線、不給錯誤狀態碼(docs/01 S5),所以自己在 280 秒收尾
            deadline = started + STREAM_CAP_S
            ok = not any("error" in chunk for chunk in head)
            try:
                for chunk in head:
                    yield _sse(chunk)
                while True:
                    remaining = deadline - time.monotonic()
                    try:
                        if remaining <= 0:
                            raise asyncio.TimeoutError
                        chunk = await asyncio.wait_for(gen.__anext__(), timeout=remaining)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        ok = False
                        yield _sse({"error": {"code": "stream_timeout", "provider_status": None,
                                              "job_id": ctx.job_id or None,
                                              "message": "串流達到單一連線上限而結束,內容可能不完整"}})
                        break
                    ok = ok and "error" not in chunk
                    yield _sse(chunk)
                yield _sse("[DONE]")
            finally:
                await gen.aclose()
                await record_usage(ctx, backend, "ok" if ok else "error", 200, started, True)

        return StreamingResponse(body(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache", "X-Accel-Buffering": "no", **headers_for(ctx)})

    async def run_chat(req: dict, caller: Caller, request: Request):
        if (req.get("model") or "").strip() == "auto":
            return await run_auto(req, caller, request)
        backend, model = route_model(req.get("model"))
        ctx = new_ctx(caller, request, model_label(req.get("model")))
        started = time.monotonic()

        if request.headers.get("x-bridge-async", "").lower() == "true":
            return await start_async(backend, model, req, ctx, started)

        if not req.get("stream"):
            try:
                result = await sync_once(backend, model, req, ctx, started)
            except AsyncAccepted as acc:
                return accepted(acc.job_key)
            except BridgeError as exc:
                await record_usage(ctx, backend, "error", exc.status, started, False)
                raise
            await record_usage(ctx, backend, "ok", 200, started, False)
            return sync_response(result, ctx)

        gen = open_stream(backend, model, req, ctx)
        # 先拿到第一段:在那之前發生的錯誤(驗證、找不到 worker、上游 4xx)回一般的錯誤回應
        try:
            head = [await gen.__anext__()]
        except StopAsyncIteration:
            head = []
        except BridgeError as exc:
            await record_usage(ctx, backend, "error", exc.status, started, True)
            raise
        return stream_response(gen, head, ctx, backend, started)

    async def start_async(backend: str, model: str, req: dict, ctx: CallContext, started: float) -> JSONResponse:
        if backend == "local":
            job = await local.create_job(ctx, req)
        else:
            task = asyncio.create_task(provider_for(backend).complete(req, model, ctx))
            job = await local.create_job(ctx, req, provider=backend)
            spawn(finish_job(job, backend, ctx, started, task))
        return JSONResponse({"id": job["key"], "status": job["status"]}, status_code=202,
                            headers={"X-Bridge-Job": job["key"]})

    def cloud_ready(label: str) -> bool:
        if not label:
            return False
        try:
            backend, _ = route_model(label)
        except BridgeError:
            return False
        return backend in provider_cache or bool(
            s.openrouter_api_key if backend == "openrouter" else s.anthropic_api_key)

    def combined(failures: list[tuple[str, BridgeError]], last: BridgeError) -> BridgeError:
        """備援也失敗時:回最後一個錯誤,訊息與標頭帶上先前失敗的是誰、為什麼。"""
        if not failures:
            return last
        before = ";".join(f"{label}:{exc.code}" for label, exc in failures)
        return BridgeError(last.status, last.code, f"{last.message}(先試的 {before} 也失敗)",
                           last.provider_status, {**last.headers, "X-Bridge-Fallback": before})

    async def run_auto(req: dict, caller: Caller, request: Request):
        """model: "auto":依使用者自己選的優先順序主備切換(bridge/routing.py)。"""
        if not caller.user:
            raise BridgeError(400, "user_required", "auto 需要使用者身分:本機那一側只替使用者本人運算")
        priority = await prefs.priority(caller.source, caller.user)
        order = routing.candidates(req, s).ordered(priority)
        body = {k: v for k, v in req.items() if k != "models"}
        started = time.monotonic()
        failures: list[tuple[str, BridgeError]] = []

        def attempt_ctx(label: str) -> CallContext:
            ctx = new_ctx(caller, request, label)
            ctx.priority = priority
            if failures:
                ctx.fallback = {"from": failures[0][0], "reason": failures[0][1].code}
            return ctx

        if request.headers.get("x-bridge-async", "").lower() == "true":
            # 非同步:當下就要決定交給誰,所以先看哪一側「現在」可用
            for side, label in order:
                available = (await local.online_worker(caller.user)) if side == "local" else cloud_ready(label)
                if available:
                    backend, model = route_model(label)
                    return await start_async(backend, model, body, attempt_ctx(label), started)
                failures.append((label, BridgeError(409, "no_worker_for_user" if side == "local"
                                                    else "provider_not_configured", "目前不可用")))
            raise combined(failures, BridgeError(503, "no_backend_available", "兩個後端目前都不可用"))

        for index, (_side, label) in enumerate(order):
            is_last = index == len(order) - 1
            ctx = attempt_ctx(label)
            try:
                backend, model = route_model(label)
            except BridgeError as exc:
                if is_last or not routing.can_fall_back(exc.code):
                    raise combined(failures, exc)
                failures.append((label, exc))
                continue

            if not req.get("stream"):
                try:
                    result = await sync_once(backend, model, body, ctx, started)
                except AsyncAccepted as acc:
                    return accepted(acc.job_key)
                except BridgeError as exc:
                    fall = not is_last and routing.can_fall_back(exc.code)
                    await record_usage(ctx, backend, "fallback" if fall else "error", exc.status, started, False)
                    if not fall:
                        raise combined(failures, exc)
                    failures.append((label, exc))
                    continue
                await record_usage(ctx, backend, "ok", 200, started, False)
                return sync_response(result, ctx)

            # 串流:在送出任何內容之前失敗才切換;一旦開始出字就不換了
            gen = open_stream(backend, model, body, ctx)
            head: list[dict] = []
            failed: BridgeError | None = None
            try:
                while True:
                    remaining = started + STREAM_CAP_S - time.monotonic()
                    if remaining <= 0:
                        break
                    chunk = await asyncio.wait_for(gen.__anext__(), timeout=remaining)
                    if "error" in chunk and not is_last and routing.can_fall_back(chunk["error"].get("code")):
                        err = chunk["error"]
                        failed = BridgeError(502, err.get("code") or "failed", err.get("message") or "")
                        break
                    head.append(chunk)
                    if is_last or "error" in chunk or _has_output(chunk):
                        break
            except StopAsyncIteration:
                pass
            except asyncio.TimeoutError:
                pass   # 到上限還沒出字:照樣回這個串流,body 會立刻送 stream_timeout 與工單 id
            except BridgeError as exc:
                if is_last or not routing.can_fall_back(exc.code):
                    await gen.aclose()
                    await record_usage(ctx, backend, "error", exc.status, started, True)
                    raise combined(failures, exc)
                failed = exc
            if failed is not None:
                await gen.aclose()
                await record_usage(ctx, backend, "fallback", failed.status, started, True)
                failures.append((label, failed))
                continue
            return stream_response(gen, head, ctx, backend, started)
        raise BridgeError(503, "no_backend_available", "沒有可用的後端")   # 不會走到這裡(至少有本機候選)

    @app.post("/v1/chat/completions")
    async def chat(request: Request):
        raw = await request.body()
        caller = await caller_of(request, raw)
        try:
            req = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise BridgeError(400, "bad_json", "請求內容不是合法 JSON") from None
        if not isinstance(req, dict) or not isinstance(req.get("messages"), list):
            raise BridgeError(400, "bad_request", "messages 必填且必須是陣列")
        return await run_chat(req, caller, request)

    @app.post("/v1/responses")
    async def responses(request: Request):
        raw = await request.body()
        caller = await caller_of(request, raw)
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise BridgeError(400, "bad_json", "請求內容不是合法 JSON") from None
        if body.get("stream"):
            raise BridgeError(400, "stream_not_supported", "/v1/responses 目前只支援非串流;要串流請用 /v1/chat/completions")
        messages = [{"role": "system", "content": body["instructions"]}] if body.get("instructions") else []
        source = body.get("input")
        if isinstance(source, str):
            messages.append({"role": "user", "content": source})
        else:
            for item in source or []:
                if isinstance(item, dict) and item.get("content"):
                    messages.append({"role": item.get("role") or "user", "content": item["content"]})
        req = {"model": body.get("model"), "messages": messages,
               "max_tokens": body.get("max_output_tokens"),
               "reasoning_effort": (body.get("reasoning") or {}).get("effort")}
        fmt = (body.get("text") or {}).get("format") or {}
        if fmt.get("type") == "json_schema":
            req["response_format"] = {"type": "json_schema", "json_schema": {"schema": fmt.get("schema")}}
        elif fmt.get("type") == "json_object":
            req["response_format"] = {"type": "json_object"}
        resp = await run_chat({k: v for k, v in req.items() if v is not None}, caller, request)
        if resp.status_code != 200:
            return resp
        data = json.loads(resp.body)
        text = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage") or {}
        return JSONResponse({
            "id": data.get("id"), "object": "response", "status": "completed", "model": data.get("model"),
            "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}],
            "output_text": text,
            "usage": {"input_tokens": usage.get("prompt_tokens", 0), "output_tokens": usage.get("completion_tokens", 0),
                      "total_tokens": usage.get("total_tokens", 0)},
        }, headers={k: v for k, v in resp.headers.items() if k.lower().startswith("x-bridge-")})

    @app.get("/v1/jobs/{job_id}")
    async def job_status(job_id: str, request: Request):
        caller = await caller_of(request, b"")
        job = await store.by_key("jobs", job_id)
        if not job or job.get("source") != caller.source or (caller.user and job.get("owner") != caller.user):
            raise BridgeError(404, "not_found", "找不到這張工單")
        status = {"pending": "pending", "leased": "running", "running": "running"}.get(job.get("status"),
                                                                                         job.get("status"))
        result = None
        stored = job.get("result_json") or {}
        if job.get("status") == "done":
            result = stored.get("completion") or _completion(job_id, stored.get("text") or "", job.get("model") or "",
                                                             usage_from_worker(stored.get("usage")),
                                                             stored.get("structured"))
        return {"id": job_id, "status": status, "result": result, "error": job.get("error_json")}

    # ── worker 面 ────────────────────────────────────────────────────────
    async def worker_of(request: Request) -> dict:
        raw = request.headers.get("authorization", "")
        key = raw[7:].strip() if raw.lower().startswith("bearer ") else ""
        if not key.startswith("bwk_"):
            raise BridgeError(401, "bad_device_key", "需要設備鑰匙")
        return await local.worker_from_key(key)

    @app.post("/worker/enroll")
    async def enroll(request: Request):
        data = await request.json()
        return await local.enroll(str(data.get("code") or ""), str(data.get("name") or "worker"),
                                  str(data.get("os") or ""), str(data.get("version") or ""),
                                  data.get("models") or [])

    @app.post("/worker/claim")
    async def claim(request: Request):
        worker = await worker_of(request)
        job = await local.claim(worker)
        return {"job": job}

    @app.post("/worker/heartbeat")
    async def heartbeat(request: Request):
        worker = await worker_of(request)
        data = await request.json()
        await local.touch(worker, {"version": str(data.get("version") or "")[:40], "models": data.get("models") or []})
        return {"ok": True, "server_version": s.version}

    @app.post("/worker/jobs/{job_id}/chunk")
    async def chunk(job_id: str, request: Request):
        worker = await worker_of(request)
        data = await request.json()
        await local.chunk(worker, job_id, str(data.get("text") or ""))
        return {"ok": True}

    @app.post("/worker/jobs/{job_id}/result")
    async def result(job_id: str, request: Request):
        worker = await worker_of(request)
        data = await request.json()
        job = await local.result(worker, job_id, data)
        ctx = CallContext(source=job.get("source") or "", user=job.get("owner") or "",
                          model_label=job.get("model") or "local/self", job_id=job_id,
                          served_by=f"local:{data.get('model') or 'claude'}")
        ctx.usage = {**usage_from_worker(data.get("usage")), "cost_usd": data.get("cost_usd") or 0}
        await record_usage(ctx, "local", "ok", 200, time.monotonic() - float(data.get("duration_ms") or 0) / 1000,
                           False)
        return {"ok": True}

    @app.post("/worker/jobs/{job_id}/fail")
    async def fail(job_id: str, request: Request):
        worker = await worker_of(request)
        await local.fail(worker, job_id, await request.json())
        return {"ok": True}

    return app
