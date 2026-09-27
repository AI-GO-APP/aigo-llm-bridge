import React, { useEffect, useState } from "react";
import { runAction } from "../lib/bridge";

type Computer = { id: string; name: string; os: string; version: string; status: string; online: boolean;
                  last_seen_at: number };

/** 連接我的電腦:產生綁定碼 → 在自己電腦上執行 worker;列出與撤銷自己的電腦。 */
export default function ConnectPage() {
  const [enroll, setEnroll] = useState<any>(null);
  const [computers, setComputers] = useState<Computer[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function refresh() {
    try {
      const res = await runAction("bridge_computers", { op: "list" });
      setComputers(res.workers || []);
      if (!res.ok) setMessage(res.error || "讀取失敗");
    } catch (e: any) {
      setMessage(String(e?.message || e));
    }
  }

  useEffect(() => { refresh(); }, []);

  async function makeCode() {
    setBusy(true);
    setMessage("");
    try {
      const res = await runAction("bridge_computers", { op: "enroll" });
      if (res.ok) setEnroll(res);
      else setMessage(res.error || "產生綁定碼失敗");
    } catch (e: any) {
      setMessage(String(e?.message || e));
    }
    setBusy(false);
  }

  async function revoke(id: string) {
    setBusy(true);
    try {
      const res = await runAction("bridge_computers", { op: "revoke", id });
      if (!res.ok) setMessage(res.error || "撤銷失敗");
      await refresh();
    } catch (e: any) {
      setMessage(String(e?.message || e));
    }
    setBusy(false);
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">連接我的電腦</h1>
        <p className="page-description">
          讓這個 app 用「你自己電腦上、你自己登入的 Claude Code」處理「你自己」送出的工作。一台電腦只服務它的主人。
        </p>
      </div>

      <div className="card mb-6">
        <div className="card-header">
          <h3 className="card-title">1. 產生綁定碼</h3>
          <p className="card-description">10 分鐘內有效,只能用一次。先確認電腦上的 Claude Code 已用你自己的帳號登入。</p>
        </div>
        <div className="card-content">
          <button className="btn btn-primary btn-sm" disabled={busy} onClick={makeCode}>產生綁定碼</button>
          {enroll && (
            <div className="mt-3" data-testid="enroll">
              <p className="text-lg font-semibold">綁定碼:<span data-testid="code">{enroll.code}</span></p>
              <p className="text-sm text-muted mt-2">
                下載 worker(單一 Python 檔,只用標準函式庫):<a href={enroll.worker_url} target="_blank" rel="noreferrer">aigo_bridge_worker.py</a>
              </p>
              <pre className="text-xs mt-2" style={{ whiteSpace: "pre-wrap" }}>{(enroll.commands || []).join("\n")}</pre>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex items-center justify-between">
            <h3 className="card-title">2. 我的電腦</h3>
            <button className="btn btn-ghost btn-sm" disabled={busy} onClick={refresh}>重新整理</button>
          </div>
        </div>
        <div className="card-content">
          {computers.length === 0 && <p className="text-sm text-muted">還沒有綁定任何電腦。</p>}
          {computers.map((c) => (
            <div key={c.id} className="flex items-center justify-between py-6" data-testid="computer">
              <span>
                <span className={c.online ? "badge badge-success" : "badge badge-outline"}>
                  {c.status === "revoked" ? "已撤銷" : c.online ? "在線" : "離線"}
                </span>{" "}
                {c.name}({c.os},worker {c.version})
              </span>
              {c.status !== "revoked" && (
                <button className="btn btn-outline btn-sm" disabled={busy} onClick={() => revoke(c.id)}>撤銷</button>
              )}
            </div>
          ))}
          {message && <p className="text-sm text-destructive mt-2" data-testid="message">{message}</p>}
        </div>
      </div>
    </div>
  );
}
