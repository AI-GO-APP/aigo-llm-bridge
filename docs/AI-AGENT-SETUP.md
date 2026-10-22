# 交給你的 AI agent

以下 prompt 適合開源 repo 或完整解壓的安裝包。使用者自己貼上後，agent 才按本次指示操作其選定的帳戶；文件本身不是部署授權。

若使用解壓的安裝包，請先把 `app` 目錄交給 AI agent，或切換到 `app` 目錄，再貼上以下 prompt；已安裝則使用版本目錄內的同一組文件。

```text
請協助我安裝與啟用這個 LLM Bridge。先讀 AGENTS.md、skills/byo-cloudflare/SKILL.md、docs/BYO-QUICKSTART.md 及 docs/DEVICE-IDENTITY.md。

先辨識 Windows／macOS 與 repo／原生 ZIP。repo 請依 docs/CROSS-PLATFORM-INSTALL.md，用 Python 3.12+ 執行 tools/install.py，之後從 source-install.json 讀專用 python、app、data_dir 與 launcher；不要把 repo 路徑當永久安裝路徑。用 doctor 檢查 Node 22+、Wrangler 及 CLI 訂閱登入。Windows 原生 ZIP 則照下段，不需要 Python。macOS 目前標記待驗證，不可宣稱可直接正式使用或已通過實機驗收。

我要 BYO Cloudflare：使用我自己的 Cloudflare 帳戶部署我這個裝置專屬的 Worker，不使用發布方的網址或憑證。請先檢查既有裝置 status 與本機 Wrangler 登入。若有多個帳戶且我未指定，再請我選擇；憑證不要貼進聊天。目標明確後，我授權你完成該帳戶內本專案的部署與配對，不購買方案或網域。

若拿到安裝包，先從包含 Install.ps1 的目錄安裝（app 的上一層）；不要只執行解壓目錄的 EXE 就聲稱安裝完成。API／CLI 模式不帶 Launch；讀 install.json 找到實際安裝 EXE、BYO-Setup 與 data_dir，不需要 Python。若做隔離驗收，使用獨立 InstallRoot 與 ShortcutDirectory，保留我的現有捷徑／啟動設定。

用隨附工具 plan 產生可檢查的專案，再 deploy。以 key-create 建立臨時 key，僅在記憶體保留回傳的明文；key-list 不顯示明文，結束用 key-revoke 撤銷。若是既有安裝，要保留原 device_id、Worker 名稱、URL、API key；不要因重新登入而新建入口。更新時以同 InstallRoot 安裝、沿用 install.json 的 data_dir，再讀新的執行路徑。Claude／Codex 訂閱登入由我自行完成，不打斷我正在使用的 CLI，也不要操作其視窗。先用 API／CLI 驗證，暫時不要 Computer Use。

請用合成資料測試 HTTPS models GET、chat POST、key 撤銷，以及只重啟 Bridge 後 URL 和同一 key 仍有效；不重開電腦。只保存 metadata，不保存原始 request／response 或明文 key。測試後撤銷測試 key，告訴我通過項目與仍需我操作的登入步驟。

預設真實測試選 Codex 模型，先以 models GET 與訂閱狀態確認；不要呼叫正在使用中的 Claude 來測試。不要聲稱任何 AI IDE 的內建 agent 都相容：須能自訂 Chat Completions base URL、關閉串流與 tools。

驗收完成後另建給我實際服務使用的長效 key：key-create --label 'My service' --handoff。此 key 保留有效，僅測試 key 要撤銷。一次性輸出直接交給我保存到服務端 secret，不存 repo／檔案或驗收紀錄。交付 public_url + /api/v1、完整 key 及 integration.prompt，讓我可複製給第三方電腦的 AI IDE／Web IDE。若要放在持久聊天，改交不含 key 的 handoff 訊息，明文 key 由我在本機管理台取得。若 Cloudflare／訂閱／macOS 主機不可用，要分開列出尚未驗證範圍，不得宣稱全流程完成。
```

repo 使用 `python tools/byo_setup.py ...`；安裝版使用 `BYO-Setup\AIGO-Bridge-Setup.exe ...`。不要將歷史報告中的實測網址當成自己的入口。
