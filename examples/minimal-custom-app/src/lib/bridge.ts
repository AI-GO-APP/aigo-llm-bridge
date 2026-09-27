/**
 * 瀏覽器端的 Bridge 客戶端(可直接複製到任何 Custom App)。
 *
 * - session token 由 Server Action `bridge_session` 換來(source 金鑰不進瀏覽器),快到期自動換新
 * - 串流直連 Bridge:Custom App 執行頁的 CSP 只允許 *.ai-go.app,Bridge 部署成 Hosted App 正好在範圍內
 * - 串流完整的判斷:收到 [DONE] 且之前沒有 error 事件(Hosted 單一請求 300 秒一到會直接斷線,不會有錯誤狀態碼)
 */

type Json = Record<string, any>;

export type BridgeSession = { token: string; exp: number; base_url: string };

export type StreamResult = {
  text: string;
  complete: boolean;          // 收到 [DONE] 且沒有 error 事件
  error?: { code: string; message: string; job_id?: string };
  servedBy?: string | null;   // 實際回答的型號(X-Bridge-Served-By)
  dropped?: string | null;    // 指定了但模型做不到、沒有送出的參數(X-Bridge-Dropped)
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

export async function streamChat(
  body: Json,
  onDelta: (text: string) => void,
  opts: { conversation?: string; signal?: AbortSignal } = {},
): Promise<StreamResult> {
  const session = await getSession();
  const t0 = performance.now();
  const headers: Record<string, string> = { Authorization: "Bearer " + session.token, "Content-Type": "application/json" };
  if (opts.conversation) headers["X-Bridge-Session"] = opts.conversation;
  const resp = await fetch(session.base_url + "/v1/chat/completions", {
    method: "POST", headers, signal: opts.signal, body: JSON.stringify({ ...body, stream: true }),
  });
  // 雲端後端在標頭就知道;local 後端要等 worker 做完,所以也會出現在最後一個 chunk 的 x_bridge
  let servedBy = resp.headers.get("X-Bridge-Served-By");
  let dropped = resp.headers.get("X-Bridge-Dropped");
  if (!resp.ok) {
    // 串流開始之前的錯誤(找不到你的 worker、參數不合法…)是一般的 JSON 錯誤回應
    const err = (await resp.json().catch(() => ({}))).error || {};
    return { text: "", complete: false, totalMs: Math.round(performance.now() - t0), servedBy, dropped,
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
  return { text, complete: sawDone && !error, error, servedBy, dropped, firstTokenMs: first,
           totalMs: Math.round(performance.now() - t0) };
}
