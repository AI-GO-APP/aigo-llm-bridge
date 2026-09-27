import React, { useEffect, useState } from "react";
import { getPriority, setPriority, Priority, PriorityView } from "../lib/bridge";

/**
 * 「優先用哪一個」的選擇卡。
 * - gate 模式:還沒選過就只顯示這張卡、不顯示子內容 —— model="auto" 在使用者選之前會被 Bridge 拒絕,
 *   所以第一次使用一定要先問。
 * - 一般模式:放在設定頁,隨時可以改。
 */
export default function PriorityChooser({ gate = false, children }: { gate?: boolean; children?: React.ReactNode }) {
  const [view, setView] = useState<PriorityView | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setView(await getPriority());
      setError("");
    } catch (e: any) {
      setError(String(e?.message || e));
    }
  }

  useEffect(() => { load(); }, []);

  async function choose(priority: Priority) {
    setBusy(true);
    try {
      setView(await setPriority(priority));
      setError("");
    } catch (e: any) {
      setError(String(e?.message || e));
    }
    setBusy(false);
  }

  if (gate && view?.priority) return <>{children}</>;
  if (gate && !view && !error) return <div className="page-container"><p className="text-sm text-muted">載入中…</p></div>;

  const card = (
    <div className="card mb-6" data-testid="priority-card">
      <div className="card-header">
        <h3 className="card-title">{gate ? "開始之前:你想優先用哪一個?" : "優先順序"}</h3>
        <p className="card-description">
          選一個優先;它不能用的時候(例如電腦沒開、雲端限流),會自動改用另一個,並在回應旁註明。之後可以在「連接我的電腦」頁改。
        </p>
      </div>
      <div className="card-content">
        <div className="grid grid-2 gap-3">
          {(view?.choices || []).map((c) => (
            <button key={c.id} data-testid={`priority-${c.id}`} disabled={busy}
                    className={view?.priority === c.id ? "btn btn-primary" : "btn btn-outline"}
                    onClick={() => choose(c.id)}>
              <span>{c.label}</span>
              <span className="text-xs text-muted" style={{ display: "block" }}>
                {c.model || "未設定模型"} · {c.available ? "目前可用" : c.id === "local" ? "電腦尚未連線" : "尚未設定"}
              </span>
            </button>
          ))}
        </div>
        {view?.priority && <p className="text-sm mt-2">目前:優先用{view.choices.find((c) => c.id === view.priority)?.label}</p>}
        {error && <p className="text-sm text-destructive mt-2" data-testid="priority-error">{error}</p>}
      </div>
    </div>
  );
  return gate ? <div className="page-container">{card}</div> : card;
}
