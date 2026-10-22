from __future__ import annotations

import json
import os
from pathlib import Path
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import urlsplit

from . import __version__, providers, secret
from .tunnel import Tunnel
from .windows import startup_enabled,set_startup
from .store import keep_default


def date(ts): return time.strftime("%m/%d %H:%M:%S",time.localtime(ts)) if ts else "—"


class App:
    def __init__(self,root,store,runtime,api,background=False,relay=None):
        self.root,self.store,self.runtime,self.api=root,store,runtime,api
        self.tunnel=Tunnel(); self.auth={}; self.closed=False
        self.relay=relay; self.last_cleanup=0
        root.title("AI GO LLM Bridge — 本機管理")
        root.geometry("1120x760"); root.minsize(960,650)
        root.configure(bg="#f3f5f9")
        style=ttk.Style(root); style.theme_use("clam")
        style.configure(".",font=("Microsoft JhengHei UI",10),background="#f3f5f9",foreground="#172238")
        style.configure("TButton",padding=(12,7)); style.configure("TNotebook.Tab",padding=(20,10))
        style.configure("Treeview",background="white",fieldbackground="white",rowheight=32,borderwidth=0)
        style.configure("Treeview.Heading",background="#e7ecf5",font=("Microsoft JhengHei UI",10,"bold"),padding=7)
        style.map("Treeview",background=[("selected","#dce8ff")],foreground=[("selected","#102955")])
        head=tk.Frame(root,bg="#14213c",height=88); head.pack(fill="x")
        tk.Label(head,text="LLM Bridge",font=("Segoe UI",23,"bold"),fg="white",bg="#14213c").pack(side="left",padx=26,pady=18)
        tk.Label(head,text="本機訂閱 · HTTPS API · 長效金鑰",fg="#bbc9e5",bg="#14213c",font=("Microsoft JhengHei UI",11)).pack(side="left",padx=10)
        self.badge=tk.Label(head,text="● 服務執行中",fg="#82e8bc",bg="#14213c",font=("Microsoft JhengHei UI",11,"bold"))
        self.badge.pack(side="right",padx=26)
        self.tabs=ttk.Notebook(root); self.tabs.pack(fill="both",expand=True,padx=22,pady=18)
        self.overview=ttk.Frame(self.tabs,padding=22); self.keys_tab=ttk.Frame(self.tabs,padding=18)
        self.logs_tab=ttk.Frame(self.tabs,padding=18); self.settings_tab=ttk.Frame(self.tabs,padding=18)
        for frame,name in ((self.overview,"總覽"),(self.keys_tab,"API 金鑰"),(self.logs_tab,"推論紀錄"),(self.settings_tab,"設定與固定網址")):
            self.tabs.add(frame,text=name)
        self.build_overview(); self.build_keys(); self.build_logs(); self.build_settings()
        footer=ttk.Frame(root); footer.pack(fill="x",padx=26,pady=(0,12))
        ttk.Label(footer,text="只保存請求中繼資料；不保存訊息、附件、回應原文或完整金鑰。",foreground="#596a80").pack(side="left")
        ttk.Label(footer,text=__version__,foreground="#7c8aa0").pack(side="right")
        root.protocol("WM_DELETE_WINDOW",self.minimize)
        self.refresh(); self.refresh_auth()
        if store.get("tunnel_name") and store.get("public_url"):
            try: self.tunnel.start(store.get("tunnel_name"))
            except ValueError: pass
        if background: root.after(100,root.iconify)

    def title(self,parent,text,description=""):
        ttk.Label(parent,text=text,font=("Microsoft JhengHei UI",16,"bold")).pack(anchor="w",pady=(0,6))
        if description: ttk.Label(parent,text=description,foreground="#607088").pack(anchor="w",pady=(0,18))

    def copy(self,text):
        self.root.clipboard_clear(); self.root.clipboard_append(text)

    def build_overview(self):
        self.title(self.overview,"你的訂閱，提供給自己的服務使用","既有服務更換 Base URL、API key 與可用模型，即可透過標準 POST／GET 呼叫。")
        group=ttk.LabelFrame(self.overview,text="API 連線",padding=18); group.pack(fill="x",pady=10)
        self.endpoint=tk.StringVar()
        ttk.Entry(group,textvariable=self.endpoint,state="readonly",font=("Consolas",12)).pack(side="left",fill="x",expand=True)
        ttk.Button(group,text="複製 Base URL",command=lambda:self.copy(self.endpoint.get())).pack(side="left",padx=(12,0))
        self.public_note=ttk.Label(self.overview,text="",foreground="#607088"); self.public_note.pack(anchor="w",pady=(0,18))
        source=ttk.LabelFrame(self.overview,text="CLI 訂閱狀態",padding=18); source.pack(fill="x",pady=8)
        self.auth_label=ttk.Label(source,text="正在檢查既有登入…",font=("Microsoft JhengHei UI",11)); self.auth_label.pack(side="left")
        ttk.Button(source,text="重新檢查",command=self.refresh_auth).pack(side="right")
        self.summary=ttk.Label(self.overview,text="",font=("Microsoft JhengHei UI",13)); self.summary.pack(anchor="w",pady=24)
        controls=ttk.Frame(self.overview); controls.pack(anchor="w")
        self.pause_button=ttk.Button(controls,text="暫停接單",command=self.pause); self.pause_button.pack(side="left",padx=(0,10))
        ttk.Button(controls,text="縮小並繼續執行",command=self.minimize).pack(side="left",padx=(0,10))
        ttk.Button(controls,text="結束 Bridge",command=self.quit).pack(side="left")
        ttk.Label(self.overview,text="執行時使用獨立 cwd 與短暫 session，不接續或操作你正在使用的 Claude Code。\n長工作使用 /bridge/v1/jobs；結果只在記憶體保留 10 分鐘。",foreground="#607088").pack(anchor="w",pady=24)

    def tree(self,parent,columns):
        frame=ttk.Frame(parent); frame.pack(fill="both",expand=True)
        tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show="headings",selectmode="browse")
        for name,label,width in columns:
            tree.heading(name,text=label); tree.column(name,width=width,minwidth=60,stretch=True)
        bar=ttk.Scrollbar(frame,orient="vertical",command=tree.yview); tree.configure(yscrollcommand=bar.set)
        tree.pack(side="left",fill="both",expand=True); bar.pack(side="right",fill="y")
        return tree

    def build_keys(self):
        self.title(self.keys_tab,"長效 API 金鑰","預設不會到期；可獨立撤銷或輪替。完整 key 只在建立時顯示一次。")
        row=ttk.Frame(self.keys_tab); row.pack(fill="x",pady=(0,14))
        ttk.Button(row,text="＋ 建立金鑰",command=self.create_key).pack(side="left")
        ttk.Button(row,text="輪替選取金鑰",command=self.rotate).pack(side="left",padx=10)
        ttk.Button(row,text="撤銷選取金鑰",command=self.revoke).pack(side="left")
        self.keys_tree=self.tree(self.keys_tab,[("label","名稱",180),("prefix","遮罩 key",190),("providers","來源",150),("rpm","每分鐘",90),("created","建立時間",140),("state","狀態",100)])

    def selected_key(self):
        selected=self.keys_tree.selection()
        if not selected: messagebox.showinfo("選取金鑰","請先選取一把金鑰。",parent=self.root); return None
        return selected[0]

    def show_token(self,token):
        window=tk.Toplevel(self.root); window.title("新金鑰 — 僅顯示一次"); window.geometry("760x210")
        frame=ttk.Frame(window,padding=22); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="請將金鑰保存到呼叫服務的 secret 設定。關閉後無法再次顯示。",wraplength=690).pack(anchor="w",pady=(0,14))
        entry=ttk.Entry(frame,font=("Consolas",11)); entry.insert(0,token); entry.configure(state="readonly"); entry.pack(fill="x")
        ttk.Button(frame,text="複製金鑰",command=lambda:self.copy(token)).pack(side="left",pady=18)
        ttk.Button(frame,text="已保存，關閉",command=window.destroy).pack(side="right",pady=18)

    def create_key(self):
        window=tk.Toplevel(self.root); window.title("建立長效 API 金鑰"); window.geometry("480x330")
        frame=ttk.Frame(window,padding=22); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="服務名稱").pack(anchor="w")
        name=ttk.Entry(frame); name.pack(fill="x",pady=(5,15))
        flags={p:tk.BooleanVar(value=True) for p in ("claude","codex")}
        for p in flags: ttk.Checkbutton(frame,text=p,variable=flags[p]).pack(anchor="w")
        ttk.Label(frame,text="每分鐘最多請求數（全機同時執行一筆）").pack(anchor="w",pady=(12,4))
        rate=ttk.Spinbox(frame,from_=1,to=600,width=10); rate.set("30"); rate.pack(anchor="w")
        def save():
            try: _,token=self.store.create_key(name.get(),[p for p,v in flags.items() if v.get()],int(rate.get()))
            except ValueError as e: messagebox.showerror("無法建立",str(e),parent=window); return
            window.destroy(); self.refresh_keys(); self.show_token(token)
        ttk.Button(frame,text="建立",command=save).pack(anchor="e",pady=18)

    def revoke(self):
        kid=self.selected_key()
        if kid and messagebox.askyesno("撤銷金鑰","撤銷後立即停止這把 key 的排隊與執行中工作。確定撤銷？",parent=self.root):
            self.store.revoke(kid); self.runtime.cancel_key(kid); self.refresh_keys()

    def rotate(self):
        kid=self.selected_key()
        if not kid: return
        if not messagebox.askyesno("輪替金鑰","舊 key 會立即失效，請同步更新呼叫服務。確定輪替？",parent=self.root): return
        try: _,token=self.store.rotate(kid)
        except ValueError as e: messagebox.showerror("無法輪替",str(e),parent=self.root); return
        self.runtime.cancel_key(kid); self.refresh_keys(); self.show_token(token)

    def refresh_keys(self):
        selected=self.keys_tree.selection()
        self.keys_tree.delete(*self.keys_tree.get_children())
        for row in self.store.keys():
            self.keys_tree.insert("","end",iid=row["id"],values=(row["label"],row["prefix"]+"…",", ".join(json.loads(row["providers"])),row["rpm"],date(row["created_ts"]),"已撤銷" if row["revoked_ts"] else "有效"))
        if selected and self.keys_tree.exists(selected[0]): self.keys_tree.selection_set(selected[0])

    def build_logs(self):
        self.title(self.logs_tab,"推論請求紀錄","包含已接受與拒絕的 POST。此處不保存或顯示訊息、附件、回應原文。")
        row=ttk.Frame(self.logs_tab); row.pack(fill="x",pady=(0,14))
        self.log_status=tk.StringVar(); self.log_provider=tk.StringVar()
        for variable,values in ((self.log_status,["","queued","running","completed","failed","rejected","cancelled","interrupted"]),(self.log_provider,["","claude","codex"])):
            combo=ttk.Combobox(row,textvariable=variable,values=values,state="readonly",width=15); combo.pack(side="left",padx=(0,10)); combo.bind("<<ComboboxSelected>>",lambda _:self.refresh_logs())
        ttk.Button(row,text="匯出中繼資料 CSV",command=self.export).pack(side="left",padx=10)
        ttk.Button(row,text="清除已結束紀錄",command=self.clear_logs).pack(side="right")
        self.logs_tree=self.tree(self.logs_tab,[("time","時間",130),("model","模型",205),("state","狀態",100),("http","HTTP",65),("ms","耗時 ms",90),("tokens","輸入／輸出 tokens",130),("error","錯誤分類",155)])

    def refresh_logs(self):
        if not hasattr(self,"logs_tree"): return
        self.logs_tree.delete(*self.logs_tree.get_children())
        for row in self.store.logs(self.log_status.get(),self.log_provider.get()):
            self.logs_tree.insert("","end",values=(date(row["created_ts"]),row["model"] or "—",row["status"],row["http_status"] or "—",row["duration_ms"] or "—",f"{row['prompt_tokens'] or 0} / {row['completion_tokens'] or 0}",row["error_code"] or "—"))

    def export(self):
        path=filedialog.asksaveasfilename(parent=self.root,defaultextension=".csv",initialfile="bridge-request-metadata.csv",filetypes=[("CSV","*.csv")])
        if path: self.store.export(path,status=self.log_status.get(),provider=self.log_provider.get())

    def clear_logs(self):
        if messagebox.askyesno("清除紀錄","只清除已結束的請求中繼資料，確定繼續？",parent=self.root):
            self.store.prune(all_finished=True); self.refresh_logs()

    def build_settings(self):
        self.title(self.settings_tab,"BYO Cloudflare 與執行設定","入口由安裝者自己的 Cloudflare 管理；裝置網址與 API key 獨立於 Claude／Codex 登入。")
        self.fields={}
        form=ttk.Frame(self.settings_tab); form.pack(fill="x")
        for i,(name,label) in enumerate((("public_url","固定公開網址（https://…）"),("tunnel_name","Cloudflare Named Tunnel 名稱／UUID"),
            ("port","本機連接埠（修改後重啟生效）"),("retention_days","紀錄保存天數"),("timeout_s","每筆工作最多秒數"),
            ("claude_path","Claude 原生執行檔（留空自動偵測）"),("codex_path","Codex 原生執行檔（留空自動偵測）"))):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky="w",pady=6,padx=(0,14))
            variable=tk.StringVar(value=str(self.store.get(name))); self.fields[name]=variable
            ttk.Entry(form,textvariable=variable).grid(row=i,column=1,sticky="ew",pady=6)
        form.columnconfigure(1,weight=1)
        row=ttk.Frame(self.settings_tab); row.pack(fill="x",pady=14)
        self.autostart=tk.BooleanVar(value=startup_enabled())
        ttk.Checkbutton(row,text="登入 Windows 後自動啟動（縮小執行）",variable=self.autostart).pack(side="left")
        ttk.Button(row,text="保存設定",command=self.save_settings).pack(side="right")
        tunnel=ttk.Frame(self.settings_tab); tunnel.pack(fill="x")
        ttk.Button(tunnel,text="啟動已設定的 Cloudflare Tunnel",command=self.start_tunnel).pack(side="left")
        ttk.Button(tunnel,text="停止本程式的 Tunnel",command=self.tunnel.stop).pack(side="left",padx=10)
        self.tunnel_label=ttk.Label(tunnel,text=""); self.tunnel_label.pack(side="left")
        relayrow=ttk.Frame(self.settings_tab); relayrow.pack(fill="x",pady=(12,0))
        self.relay_enabled=tk.BooleanVar(value=self.store.get("relay_enabled"))
        ttk.Checkbutton(relayrow,text="啟用 Cloudflare workers.dev HTTPS 轉接",variable=self.relay_enabled).pack(side="left")
        ttk.Button(relayrow,text="設定裝置配對 key",command=self.pair_relay).pack(side="right")
        ttk.Label(self.settings_tab,text="請依隨附 BYO 指南部署自己的 Worker；發布方不代管入口或訂閱憑證。\n切換 Claude／Codex 帳號不更換網址或 key；請先暫停接單並等待工作完成。",foreground="#607088").pack(anchor="w",pady=14)
        models=ttk.LabelFrame(self.settings_tab,text="模型登錄（每行：OpenRouter slug | claude 或 codex | 原生模型 ID）",padding=10); models.pack(fill="both",expand=True)
        self.model_text=tk.Text(models,height=4,font=("Consolas",10),wrap="none"); self.model_text.pack(fill="both",expand=True)
        self.model_text.insert("1.0","\n".join(f"{m['id']} | {m['provider']} | {m['native']}" for m in self.store.get("models")))
        ttk.Label(models,text="第一行作為省略 model 時的預設；登錄不代表訂閱一定有模型權限。",foreground="#607088").pack(anchor="w",pady=(5,0))

    def save_settings(self):
        try:
            values={name:v.get().strip() for name,v in self.fields.items()}
            for name,low,high in (("port",1024,65535),("retention_days",1,365),("timeout_s",10,1800)):
                values[name]=int(values[name])
                if not low<=values[name]<=high: raise ValueError(f"{name} 必須介於 {low}–{high}。")
            if values["public_url"]:
                url=urlsplit(values["public_url"])
                if url.scheme!="https" or not url.hostname or url.path not in {"","/"} or url.query or url.fragment or url.username:
                    raise ValueError("公開網址請只填 HTTPS origin，不含 /api/v1、帳密或 query。")
                values["public_url"]=values["public_url"].rstrip("/")
            models=[]
            for line in self.model_text.get("1.0","end").splitlines():
                if not line.strip(): continue
                parts=[p.strip() for p in line.split("|")]
                if len(parts)!=3 or parts[1] not in {"claude","codex"} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:-]{0,120}",parts[0]) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,100}",parts[2]):
                    raise ValueError("模型登錄格式無效。")
                models.append(dict(zip(("id","provider","native"),parts)))
            if not models or len({m["id"] for m in models})!=len(models): raise ValueError("請至少登錄一個模型，且 slug 不可重複。")
            if os.name=="nt": set_startup(self.autostart.get(),self.store.directory)
            for name,value in values.items(): self.store.set(name,value)
            default=keep_default(models,self.store.get('default_model'))
            self.store.set("models",models); self.store.set("default_model",default); self.store.prune()
            self.store.set("relay_enabled",self.relay_enabled.get())
            if self.relay:
                self.relay.stop()
                if self.relay_enabled.get(): self.relay.start()
        except (ValueError,OSError) as error:
            messagebox.showerror("設定未保存",str(error),parent=self.root); return
        messagebox.showinfo("已保存","key 與設定會在重啟後保留。連接埠修改需重開 Bridge。",parent=self.root)

    def start_tunnel(self):
        try: self.tunnel.start(self.fields["tunnel_name"].get().strip())
        except ValueError as error: messagebox.showerror("無法啟動 Tunnel",str(error),parent=self.root)

    def pair_relay(self):
        from tkinter import simpledialog
        value=simpledialog.askstring("裝置配對 key","輸入 Cloudflare Worker 的 DEVICE_KEY（會以 Windows DPAPI 加密保存）：",show="*",parent=self.root)
        if value:
            try: secret.save(self.store.directory,value)
            except ValueError as error: messagebox.showerror("無法保存",str(error),parent=self.root)

    def refresh_auth(self):
        def work():
            values={p:providers.status(p,self.store) for p in ("claude","codex")}
            self.auth=values
        threading.Thread(target=work,daemon=True).start()

    def pause(self): self.store.set("accepting",not self.store.get("accepting"))

    def refresh(self):
        if self.closed: return
        if time.monotonic()-self.last_cleanup>60:
            self.store.prune()
            with self.runtime.lock: self.runtime.cleanup()
            self.last_cleanup=time.monotonic()
        accepting=self.store.get("accepting")
        self.badge.configure(text="● 接受請求" if accepting else "● 暫停接單",fg="#82e8bc" if accepting else "#ffcb7c")
        self.pause_button.configure(text="暫停接單" if accepting else "恢復接單")
        public=self.store.get("public_url")
        self.endpoint.set((public or f"http://127.0.0.1:{self.api.port}")+"/api/v1")
        self.public_note.configure(text=("BYO 裝置 "+self.store.get('device_id')[:12]+" · 切換訂閱帳號保留此入口與 key。") if public else "尚未部署你自己的 Cloudflare Worker；請將隨附 AGENT-SETUP prompt 交給 AI agent。")
        if self.auth:
            self.auth_label.configure(text="     ".join(f"{p}: {'已登入訂閱' if s['ready'] else '未就緒'}" for p,s in self.auth.items()))
        logs=self.store.logs(limit=1000)
        self.summary.configure(text=f"有效金鑰 {sum(not r['revoked_ts'] for r in self.store.keys())}   ·   排隊／執行 {sum(r['status'] in {'queued','running'} for r in logs)}   ·   最近完成 {sum(r['status']=='completed' for r in logs)}")
        self.tunnel_label.configure(text=("Relay: "+self.relay.state) if self.relay and self.store.get("relay_enabled") else self.tunnel.state)
        self.refresh_keys(); self.refresh_logs()
        self.root.after(2500,self.refresh)

    def minimize(self): self.root.iconify()
    def quit(self):
        self.closed=True; self.root.withdraw(); self.tunnel.stop()
        if self.relay: self.relay.stop()
        def shutdown():
            self.runtime.stop(); self.api.stop()
            self.root.after(0,self.root.destroy)
        threading.Thread(target=shutdown,daemon=True).start()
