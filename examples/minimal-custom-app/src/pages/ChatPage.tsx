import React, { useState } from "react";
import { runAction, streamChat, StreamResult } from "../lib/bridge";

const MODELS = ["local/self", "local/self:haiku", "local/self:sonnet", "local/self:opus"];

function newConversation(): string {
  return (crypto as any).randomUUID ? (crypto as any).randomUUID() : String(Date.now());
}

/** 對話:瀏覽器直連 Bridge 串流;模型、effort、thinking 每次自己指定(沒指定就照模型原本的行為)。 */
export default function ChatPage() {
  const [model, setModel] = useState(MODELS[0]);
  const [customModel, setCustomModel] = useState("");
  const [effort, setEffort] = useState("");
  const [thinkingOff, setThinkingOff] = useState(false);
  const [keepConversation, setKeepConversation] = useState(false);
  const [conversation, setConversation] = useState(newConversation());
  const [prompt, setPrompt] = useState("用一句話介紹你自己。");
  const [output, setOutput] = useState("");
  const [meta, setMeta] = useState<StreamResult | null>(null);
  const [serverResult, setServerResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  function body() {
    const chosen = customModel.trim() ? `local/self:${customModel.trim()}` : model;
    const b: Record<string, any> = { model: chosen, messages: [{ role: "user", content: prompt }] };
    if (effort) b.reasoning_effort = effort;
    if (thinkingOff) b.reasoning = { enabled: false };
    return b;
  }

  async function sendStream() {
    setBusy(true);
    setOutput("");
    setMeta(null);
    try {
      const res = await streamChat(body(), setOutput, { conversation: keepConversation ? conversation : undefined });
      setMeta(res);
    } catch (e: any) {
      setMeta({ text: "", complete: false, totalMs: 0, error: { code: "client", message: String(e?.message || e) } });
    }
    setBusy(false);
  }

  async function sendServer() {
    setBusy(true);
    setServerResult(null);
    try {
      setServerResult(await runAction("bridge_chat", body()));
    } catch (e: any) {
      setServerResult({ ok: false, error: String(e?.message || e) });
    }
    setBusy(false);
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">對話</h1>
        <p className="page-description">由你電腦上的 Claude Code 回答。模型、effort、thinking 都可以逐次指定。</p>
      </div>

      <div className="card mb-6">
        <div className="card-content">
          <div className="grid grid-3 gap-3">
            <label className="form-group">模型
              <select value={model} onChange={(e) => setModel(e.target.value)} data-testid="model">
                {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
              </select>
            </label>
            <label className="form-group">或完整模型 ID(選填)
              <input value={customModel} onChange={(e) => setCustomModel(e.target.value)} placeholder="例 claude-opus-5"
                     data-testid="custom-model" />
            </label>
            <label className="form-group">effort
              <select value={effort} onChange={(e) => setEffort(e.target.value)} data-testid="effort">
                <option value="">預設(照模型)</option>
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>
          </div>
          <div className="flex gap-4 mt-2">
            <label><input type="checkbox" checked={thinkingOff} onChange={(e) => setThinkingOff(e.target.checked)}
                          data-testid="thinking-off" /> 關閉 thinking</label>
            <label><input type="checkbox" checked={keepConversation}
                          onChange={(e) => setKeepConversation(e.target.checked)} data-testid="keep" /> 延續對話</label>
            {keepConversation && (
              <button className="btn btn-link btn-sm" onClick={() => setConversation(newConversation())}>開新對話</button>
            )}
          </div>
          <textarea className="w-full mt-3" rows={3} value={prompt} onChange={(e) => setPrompt(e.target.value)}
                    data-testid="prompt" />
          <div className="flex gap-2 mt-2">
            <button className="btn btn-primary btn-sm" disabled={busy} onClick={sendStream} data-testid="send">送出(串流)</button>
            <button className="btn btn-outline btn-sm" disabled={busy} onClick={sendServer} data-testid="send-server">
              從伺服器端送出
            </button>
          </div>
        </div>
      </div>

      <div className="card mb-6">
        <div className="card-header"><h3 className="card-title">回應</h3></div>
        <div className="card-content">
          <pre data-testid="output" style={{ whiteSpace: "pre-wrap" }}>{output || "—"}</pre>
          {meta && (
            <p className="text-xs text-muted mt-2" data-testid="meta">
              {meta.complete ? "完整" : "不完整"} · 第一段 {meta.firstTokenMs ?? "—"} ms · 全部 {meta.totalMs} ms
              · 實際型號 {meta.servedBy || "—"}{meta.dropped ? ` · 未套用:${meta.dropped}` : ""}
            </p>
          )}
          {meta?.error && (
            <p className="text-sm text-destructive mt-2" data-testid="error">
              {meta.error.message}({meta.error.code}){meta.error.job_id ? ` 工單 ${meta.error.job_id}` : ""}
            </p>
          )}
        </div>
      </div>

      {serverResult && (
        <div className="card">
          <div className="card-header"><h3 className="card-title">伺服器端呼叫的結果</h3></div>
          <div className="card-content">
            <pre className="text-xs" data-testid="server-result" style={{ whiteSpace: "pre-wrap" }}>
              {JSON.stringify(serverResult, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
