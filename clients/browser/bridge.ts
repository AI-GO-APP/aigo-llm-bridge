/**
 * aigo-llm-bridge 的瀏覽器客戶端(Custom App 前端用;整個檔案複製到 src/lib/bridge.ts)。
 *
 * - session token 由 Server Action `bridge_session` 換來(source 金鑰不進瀏覽器),快到期自動換新
 * - 串流直連 Bridge:Custom App 執行頁的 CSP 只允許 *.ai-go.app,Bridge 部署成 Hosted App 正好在範圍內
 * - 串流完整的判斷:收到 [DONE] 且之前沒有 error 事件(Hosted 單一請求 300 秒一到會直接斷線,不會有錯誤狀態碼)
 * - model 預設 "auto":依使用者自己選的優先順序,在「我的電腦(Claude Code)」與「雲端(OpenRouter)」之間主備切換;
 *   還沒選過會得到 code = "priority_required",畫面要先問使用者(getPriority / setPriority)
 *
 * 正本在 clients/browser/bridge.ts;examples/ 裡的副本由 CI 檢查必須一字不差。
 */

type Json = Record<string, any>;

export type BridgeSession = { token: string; exp: number; base_url: string };

export type Priority = "local" | "cloud";

export type PriorityView = {
  priority: Priority | null;          // null = 還沒問過使用者
  updated_at: number | null;
  choices: { id: Priority; label: string; model: string | null; available: boolean }[];
};

export type Fallback = { from: string; reason: string } | null;

export type StreamResult = {
  text: string;
  complete: boolean;                  // 收到 [DONE] 且沒有 error 事件
  error?: { code: string; message: string; job_id?: string };
  servedBy?: string | null;           // 實際回答的型號
  dropped?: string | null;            // 指定了但模型做不到、沒有送出的參數
  priority?: Priority | null;         // auto:使用者選的優先
  fallback?: Fallback;                // auto:優先的那個失敗、改用了備援
  firstTokenMs?: number;
  totalMs: number;
};

/** 與平台 SDK 相同的網址與標頭,但回傳完整信封(SDK 在逾時時只回 data:null,看不到原因)。 */
export async function runAction(name: string, params: Json = {}): Promise<Json> {
  const w = window as any;
  const url = (w.__API_BASE__ || "/api/v1") + "/actions/apps/" + (w.__APP_ID__ || "") + "/run/" + name;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (w.__APP_TOKEN__) headers["Authorization"] = "Bearer " + w.__APP_TOKEN__;
  const resp = await fetch(url, { method: "POST", headers, credentials: "include", body: JSON.stringify({ params }) });
  const envelope = await resp.json().catch(() => ({}));
  if (!resp.ok || envelope.status === "error" || envelope.status === "timeout") {
    throw new Error(envelope.error || envelope.detail || `Action ${name} 失敗(${resp.status})`);
  }
  return envelope.result ?? {};
}

let cached: BridgeSession | null = null;

export async function getSession(): Promise<BridgeSession> {
  if (cached && cached.exp * 1000 - Date.now() > 120_000) return cached;
  const res = await runAction("bridge_session");
  if (!res.ok) throw new Error(res.error || "換 session token 失敗");
  cached = { token: res.token, exp: res.exp, base_url: res.base_url };
  return cached;
}

async function bridgeFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const session = await getSession();
  const headers = { Authorization: "Bearer " + session.token, "Content-Type": "application/json",
                    ...(init.headers as Record<string, string> | undefined) };
  return fetch(session.base_url + path, { ...init, headers });
}

async function jsonOrThrow(resp: Response): Promise<Json> {
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const err = data.error || {};
    const e = new Error(err.message || `HTTP ${resp.status}`) as Error & { code?: string };
    e.code = err.code || String(resp.status);
    throw e;
  }
  return data;
}

/** 讀使用者的優先順序與兩個選項目前是否可用。priority 是 null 代表要先問使用者。 */
export async function getPriority(): Promise<PriorityView> {
  return (await jsonOrThrow(await bridgeFetch("/bridge/preferences"))) as PriorityView;
}

export async function setPriority(priority: Priority): Promise<PriorityView> {
  const resp = await bridgeFetch("/bridge/preferences", { method: "PUT", body: JSON.stringify({ priority }) });
  return (await jsonOrThrow(resp)) as PriorityView;
}

/** 查工單(串流到上限、或伺服器端回 202 之後用)。 */
export async function getJob(jobId: string): Promise<Json> {
  return jsonOrThrow(await bridgeFetch("/v1/jobs/" + encodeURIComponent(jobId)));
}

function parseFallback(value: string | null): Fallback {
  if (!value) return null;
  const at = value.lastIndexOf(":");
  return at > 0 ? { from: value.slice(0, at), reason: value.slice(at + 1) } : { from: value, reason: "" };
}

export async function streamChat(
  body: Json,
  onDelta: (text: string) => void,
  opts: { conversation?: string; signal?: AbortSignal } = {},
): Promise<StreamResult> {
  const t0 = performance.now();
  const headers: Record<string, string> = {};
  if (opts.conversation) headers["X-Bridge-Session"] = opts.conversation;
  const resp = await bridgeFetch("/v1/chat/completions", {
    method: "POST", headers, signal: opts.signal, body: JSON.stringify({ model: "auto", ...body, stream: true }),
  });
  // 雲端後端在標頭就知道;local 後端要等 worker 做完,所以也會出現在最後一個 chunk 的 x_bridge
  let servedBy = resp.headers.get("X-Bridge-Served-By");
  let dropped = resp.headers.get("X-Bridge-Dropped");
  const priority = (resp.headers.get("X-Bridge-Priority") as Priority | null) || null;
  const fallback = parseFallback(resp.headers.get("X-Bridge-Fallback"));
  if (!resp.ok) {
    // 串流開始之前的錯誤(還沒選優先順序、參數不合法、兩個後端都失敗…)是一般的 JSON 錯誤回應
    const err = (await resp.json().catch(() => ({}))).error || {};
    return { text: "", complete: false, totalMs: Math.round(performance.now() - t0), servedBy, dropped,
             priority, fallback,
             error: { code: err.code || String(resp.status), message: err.message || `HTTP ${resp.status}` } };
  }

  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "", text = "", sawDone = false, first: number | undefined;
  let error: StreamResult["error"];
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      for (const line of block.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") { sawDone = true; continue; }
        const event = JSON.parse(data);
        if (event.error) { error = event.error; continue; }
        if (event.x_bridge) {
          servedBy = event.x_bridge.served_by || servedBy;
          if (event.x_bridge.dropped?.length) dropped = event.x_bridge.dropped.join(",");
        }
        const piece = event.choices?.[0]?.delta?.content;
        if (piece) {
          if (first === undefined) first = Math.round(performance.now() - t0);
          text += piece;
          onDelta(text);
        }
      }
    }
  }
  return { text, complete: sawDone && !error, error, servedBy, dropped, priority, fallback, firstTokenMs: first,
           totalMs: Math.round(performance.now() - t0) };
}
