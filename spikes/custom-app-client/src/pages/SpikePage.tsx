import React, { useState } from "react";

/**
 * P1 實測頁(S2、S3)。
 *
 * S2  瀏覽器能不能從 Custom App 執行頁直連 Bridge 的 SSE:
 *     ① 經 Server Action 換短效 token ② 直連串流並量首段與總時間
 *     ③ 用壞掉的 token 打一次,確認錯誤回應瀏覽器讀得到(CORS 標頭有帶)
 *     ④ 撐一條長連線,量平台多久會切斷
 * S3  Server Action 經 egress 同步呼叫 Bridge,伺服端延遲逐步拉長,找出截斷點。
 *
 * 結果都累積在頁面底部的 JSON,可以一鍵複製。
 */

type Json = Record<string, any>;

/** 與平台 SDK 同一個網址與標頭,但回傳完整信封(SDK 在逾時時只回 data:null,看不到 status)。 */
async function runActionRaw(name: string, params: Json = {}) {
  const w = window as any;
  const url = (w.__API_BASE__ || "/api/v1") + "/actions/apps/" + (w.__APP_ID__ || "") + "/run/" + name;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (w.__APP_TOKEN__) headers["Authorization"] = "Bearer " + w.__APP_TOKEN__;
  const t0 = performance.now();
  const resp = await fetch(url, { method: "POST", headers, credentials: "include", body: JSON.stringify({ params }) });
  const envelope = await resp.json().catch(() => ({}));
  return { http: resp.status, envelope, wall_ms: Math.round(performance.now() - t0) };
}

/** 讀一條 OpenAI 形狀的 SSE,回傳時間與內容。 */
async function readSse(resp: Response, t0: number, onEvent?: (j: Json) => void) {
  const reader = resp.body!.getReader();
  const dec = new TextDecoder();
  let buf = "";
  let first: number | null = null;
  let events = 0;
  let text = "";
  let last: Json | null = null;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      for (const line of block.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6);
        if (data === "[DONE]") continue;
        const j = JSON.parse(data);
        if (first === null) first = performance.now() - t0;
        events++;
        text += j.choices?.[0]?.delta?.content || "";
        last = j;
        onEvent?.(j);
      }
    }
  }
  return { first_event_ms: first === null ? null : Math.round(first), total_ms: Math.round(performance.now() - t0), events, text, last };
}

export default function SpikePage() {
  const [session, setSession] = useState<Json | null>(null);
  const [log, setLog] = useState<Json[]>([]);
  const [busy, setBusy] = useState<string>("");
  const [live, setLive] = useState<string>("");

  const record = (entry: Json) => setLog((prev) => [...prev, { at: new Date().toISOString(), ...entry }]);

  async function getSession() {
    setBusy("session");
    try {
      const r = await runActionRaw("spike_session");
      const data = r.envelope?.result;
      record({ test: "S2-session", http: r.http, status: r.envelope?.status, wall_ms: r.wall_ms,
               ok: data?.ok, error: data?.error || r.envelope?.error, exp: data?.exp, base_url: data?.base_url });
      if (data?.ok) setSession(data);
    } catch (e: any) {
      record({ test: "S2-session", error: String(e?.message || e) });
    }
    setBusy("");
  }

  async function streamDirect() {
    if (!session) return;
    setBusy("stream");
    setLive("");
    const t0 = performance.now();
    try {
      const resp = await fetch(session.base_url + "/v1/chat/completions", {
        method: "POST",
        headers: { Authorization: "Bearer " + session.token, "Content-Type": "application/json" },
        body: JSON.stringify({ model: "spike/echo", stream: true, messages: [{ role: "user", content: "ping" }],
                               spike: { tokens: 30, interval_ms: 100 } }),
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status + " " + (await resp.text()));
      const r = await readSse(resp, t0, (j) => setLive((s) => s + (j.choices?.[0]?.delta?.content || "")));
      record({ test: "S2-stream", origin: window.location.origin, ok: r.events === 31, first_event_ms: r.first_event_ms,
               total_ms: r.total_ms, events: r.events, server: r.last?.spike });
    } catch (e: any) {
      record({ test: "S2-stream", origin: window.location.origin, ok: false,
               error: String(e?.message || e), elapsed_ms: Math.round(performance.now() - t0) });
    }
    setBusy("");
  }

  async function badToken() {
    if (!session) return;
    setBusy("bad");
    try {
      const resp = await fetch(session.base_url + "/v1/chat/completions", {
        method: "POST",
        headers: { Authorization: "Bearer not-a-real-token", "Content-Type": "application/json" },
        body: JSON.stringify({ stream: true }),
      });
      record({ test: "S2-bad-token", readable_status: resp.status, body: (await resp.text()).slice(0, 120),
               ok: resp.status === 401 });
    } catch (e: any) {
      // 走到這裡代表瀏覽器看不到錯誤回應(通常是錯誤回應沒帶 CORS 標頭)
      record({ test: "S2-bad-token", ok: false, error: String(e?.message || e) });
    }
    setBusy("");
  }

  async function holdLong(seconds: number) {
    if (!session) return;
    setBusy("hold");
    const t0 = performance.now();
    let lastN = 0;
    try {
      const resp = await fetch(`${session.base_url}/v1/sse-hold?seconds=${seconds}`, {
        headers: { Authorization: "Bearer " + session.token },
      });
      const r = await readSse(resp, t0, (j) => { lastN = j.n; setLive(`長連線第 ${j.n} 次心跳,${j.elapsed_s} 秒`); });
      record({ test: "S2-hold", requested_s: seconds, ended_after_s: Math.round(r.total_ms / 1000),
               heartbeats: r.events, completed: r.events >= Math.floor(seconds / 5) });
    } catch (e: any) {
      record({ test: "S2-hold", requested_s: seconds, ok: false, last_heartbeat: lastN,
               ended_after_s: Math.round((performance.now() - t0) / 1000), error: String(e?.message || e) });
    }
    setBusy("");
  }

  async function syncSweep() {
    setBusy("sweep");
    for (const delay of [1000, 5000, 9000, 11000, 15000, 20000, 25000, 29000, 31000, 45000]) {
      setLive(`S3:伺服端延遲 ${delay} ms…`);
      try {
        const r = await runActionRaw("spike_sync", { delay_ms: delay });
        const res = r.envelope?.result;
        record({ test: "S3-sync", delay_ms: delay, http: r.http, status: r.envelope?.status, wall_ms: r.wall_ms,
                 action_elapsed_ms: res?.elapsed_ms, server_slept_ms: res?.server_slept_ms,
                 ok: !!res?.ok, error: r.envelope?.error || res?.detail || null,
                 duration_ms: r.envelope?.duration_ms });
      } catch (e: any) {
        record({ test: "S3-sync", delay_ms: delay, ok: false, error: String(e?.message || e) });
      }
    }
    setLive("");
    setBusy("");
  }

  const resultJson = JSON.stringify(log, null, 2);

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">LLM Bridge · P1 實測</h1>
        <p className="page-description">S2:瀏覽器直連 Bridge 串流 · S3:Server Action 同步上限</p>
      </div>

      <div className="grid grid-2 mb-6">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">S2 · 直連串流</h3>
            <p className="card-description">
              {session ? `token 已取得,到期 ${new Date(session.exp * 1000).toLocaleTimeString()}` : "先換 token"}
            </p>
          </div>
          <div className="card-content flex flex-wrap gap-2">
            <button className="btn btn-primary btn-sm" disabled={!!busy} onClick={getSession}>① 換 token</button>
            <button className="btn btn-outline btn-sm" disabled={!!busy || !session} onClick={streamDirect}>② 直連串流</button>
            <button className="btn btn-outline btn-sm" disabled={!!busy || !session} onClick={badToken}>③ 壞 token</button>
            <button className="btn btn-outline btn-sm" disabled={!!busy || !session} onClick={() => holdLong(330)}>④ 長連線 330 秒</button>
          </div>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">S3 · 同步上限</h3>
            <p className="card-description">伺服端延遲 1 → 45 秒,逐一從 Server Action 呼叫</p>
          </div>
          <div className="card-content">
            <button className="btn btn-primary btn-sm" disabled={!!busy} onClick={syncSweep}>開始掃描</button>
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h3 className="card-title">即時</h3>
          <p className="card-description">{busy ? `執行中:${busy}` : "閒置"}</p>
        </div>
        <div className="card-content text-sm" data-testid="live">{live || "—"}</div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h3 className="card-title">結果({log.length})</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => navigator.clipboard?.writeText(resultJson)}>複製 JSON</button>
          </div>
        </div>
        <div className="card-content">
          <pre data-testid="results" className="text-xs" style={{ whiteSpace: "pre-wrap", maxHeight: 480, overflowY: "auto" }}>
            {resultJson}
          </pre>
        </div>
      </div>
    </div>
  );
}
