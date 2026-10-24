# 交給你的 AI agent

Windows 的 [安裝 onboarding](ONBOARDING.md) 與 Mac 的 [原生五步設定](MACOS-SETUP.md) 另提供依實際安裝路徑生成的 AI IDE prompt。部署協作者是使用者選定的 AI IDE，不呼叫本地模型 CLI 當部署 agent；CLI 只用於官方授權／狀態／推論服務。新安裝的電源權限必須本人明確同意，不能因文件含指令就自動取消 owner 電腦鎖定。完成者日常啟動不重跑；CI/CD／Release 見產品入口。

這份 prompt 是使用者可複製的安裝請求範本；文件本身不授權部署。適用 Windows Setup、Mac Release source ZIP、repo 或既有安裝。Windows 的文件位於 frozen runtime 的 `_internal` 資源內，CLI 在同一版本的 `current/aigo-bridge.exe`；原始碼安裝由 source-install.json 尋找位置，不假設舊 ZIP 的 BYO-Setup 永遠存在。

```text
請協助安裝與啟用 Local Token Buffet Bridge。先讀 AGENTS.md、docs/README.md、skills/byo-cloudflare/SKILL.md、docs/BYO-QUICKSTART.md、docs/DEVICE-IDENTITY.md。所有規格／schema／API／設計／決策／驗收以 repo 文件為準，不從聊天記憶猜測。

先辨識 OS、來源安裝／舊 ZIP／Windows Velopack Setup 及既有 profile。Windows 新安裝優先 Setup，CLI 是實際安裝目錄 current/aigo-bridge.exe；先 version 確認 package，然後 setup，或 byo doctor／plan／deploy。所有指令沿用同一 data-dir，不把原始碼 clone 當永久安裝路徑。repo source 安裝依 CROSS-PLATFORM-INSTALL，用 source-install.json 的專用 Python、app、data_dir；舊 ZIP 才用 Install.ps1 與 BYO-Setup。Mac 優先從 macos-source-v… Release 下載現行 BYO ZIP 與 SHA256，驗 hash、解壓，Python 3.12+ 執行 Install.command／tools/install.py；讀 source-install.json，再開 Bridge.command 進五步原生精靈。Mac 依 MACOS-SETUP／MACOS-RELEASE 與獨立實機報告判定，不能用 Windows 結果宣稱通過；不使用歷史 desktop-macos 包。

我要 BYO Cloudflare，使用我自己的帳戶為此裝置部署專屬 Worker。先查 status 與本機 Wrangler 登入；多個帳戶且未指定才請我選，不索取／貼出 token 或 Global API key。明確目標後，我授權部署與配對本專案，不購買方案或網域。用 plan 產生可檢查的專案，再 deploy；不直接部署 repo wrangler 範本，不用歷史報告網址或發布者憑證。

既有安裝保留 device_id、Worker 名稱、固定 URL、API KEY、metadata 與平台配對憑證（Windows DPAPI／Mac 登入 Keychain）。Windows 日常程式更新用 update check／apply／status，不需重佈署 Worker；舊 ZIP 接管依 WINDOWS-INSTALL-UPDATE 的 adopt 流程。不要因重新登入而重建入口或輪替 KEY。Mac 更新依 MACOS-RELEASE 先 pause／wait-idle／停止，再以新來源更新相同 install-root／data-dir，驗原 KEY／URL／模型／容量保留。Mac／Cloud 不屬於 Windows 更新的附帶工作。

Claude／Codex 訂閱由我自行登入，不操作既有視窗、不 logout/login、不改全域設定。預設使用 Codex 做合成推論，不呼叫我正在使用的 Claude。Mac 同機只能一個 runtime，同 profile 重開只喚回視窗；另一 profile 必須先正常停止原服務。按 X 只關管理台，明確結束才停止，mac_service.py stop 可先排空。先用 API／CLI，不重開電腦；需要 UI 驗證再列明範圍。

用專用臨時 KEY 真測 HTTPS models GET、非串流 chat POST、數值 usage.cost、撤銷，以及只重啟 Bridge 後同 URL／同 KEY 仍有效。原始 request／response 與完整 KEY 不落磁碟，僅保留 allowlist metadata。未知結果不盲目重試，依 UUID 查 receipt。測試 KEY 結束撤銷；更新驗收不能重建新 KEY 冒充舊 KEY 保留。

新安裝驗收後另建 owner 服務長效 KEY；既有更新保留原 owner KEY，不強制另建：Windows Setup 使用 byo key-create --label 'My service' --handoff；source helper 直接 key-create。新 KEY 預設兩來源全開，仍受登錄模型／訂閱限制。owner KEY 保留有效，只撤銷測試 KEY。一次性結果交 owner 放服務端 secret，不寫 repo／報告；持久聊天只提供不含 KEY 的 handoff，完整 KEY 在本機一次性介面取得。

交付固定 public_url + /api/v1、有效長效 KEY 與 integration.prompt。只承諾支援的 Chat Completions 子集：可關串流、移除抽樣／token上限；tools 是呼叫端執行的提案，不是本機工具；Responses 未支援。列出真實通過／未驗證／需要 owner 完成的登入，不能只以 HTTP 200 或 source tests 聲稱安裝交付完成。

若我的既有服務使用 Jev，讀取 JEV-COMPATIBILITY.md，交付完整 /api/alpha/decisions URL、Bridge KEY、實際 model，保留原 state／questions／criteria／provider.data_collection 與 answers 解析。驗證三種題型、實際模型成本及 partial billing receipt；機率為一般 LLM 估計，業務門檻未校準。模型能力 GET／refresh 不推論，probe 會消耗額度，不能在模型選單偷偷測所有模型。新公開路徑需 Worker／Relay／Bridge 同步；只在 owner 明確授權時部署原 Worker，不換 URL／KEY、不任意呼叫正在使用的 Claude。
```

工具入口：[Windows Setup／CLI](WINDOWS-INSTALL-UPDATE.md)、[source 安裝](CROSS-PLATFORM-INSTALL.md)、[完整 API](API.md)。不要將歷史報告中的網址或配對資料當成新裝置預設。


標準容量為每裝置最多受理 64 筆（驗證、排隊與執行合計），Claude／Codex 與 Chat／Decisions 共用。執行數可低於受理數；以裝置目前 handoff／health 容量為準。請以普通同步 API 並行 POST（async/await、Promise.all 或連線池），每筆直接取得結果；串接不需工單或輪詢。新 key 預設 600 RPM，既有 key 頻率另行核對。超過 64 尚待驗證，詳見 [併發規格](CONCURRENCY.md)。
