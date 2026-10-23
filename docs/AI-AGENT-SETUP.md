# 交給你的 AI agent

這份 prompt 是使用者可複製的安裝請求範本；文件本身不授權部署。適用 repo 或已安裝的 Windows 包。Windows 的文件位於 frozen runtime 的 `_internal` 資源內，CLI 在同一版本的 `current/aigo-bridge.exe`；原始碼安裝由 source-install.json 尋找位置，不假設舊 ZIP 的 BYO-Setup 永遠存在。

```text
請協助安裝與啟用這個 LLM Bridge。先讀 AGENTS.md、docs/README.md、skills/byo-cloudflare/SKILL.md、docs/BYO-QUICKSTART.md、docs/DEVICE-IDENTITY.md。所有規格／schema／API／設計／決策／驗收以 repo 文件為準，不從聊天記憶猜測。

先辨識 OS、來源安裝／舊 ZIP／Windows Velopack Setup 及既有 profile。Windows 新安裝優先 Setup，CLI 是實際安裝目錄 current/aigo-bridge.exe；先 version 確認 package，然後 setup，或 byo doctor／plan／deploy。所有指令沿用同一 data-dir，不把原始碼 clone 當永久安裝路徑。repo source 安裝依 CROSS-PLATFORM-INSTALL，用 source-install.json 的專用 Python、app、data_dir；舊 ZIP 才用 Install.ps1 與 BYO-Setup。Mac 由 Mac 流程與實機報告獨立判定，不能用 Windows 結果宣稱通過。

我要 BYO Cloudflare，使用我自己的帳戶為此裝置部署專屬 Worker。先查 status 與本機 Wrangler 登入；多個帳戶且未指定才請我選，不索取／貼出 token 或 Global API key。明確目標後，我授權部署與配對本專案，不購買方案或網域。用 plan 產生可檢查的專案，再 deploy；不直接部署 repo wrangler 範本，不用歷史報告網址或發布者憑證。

既有安裝保留 device_id、Worker 名稱、固定 URL、API KEY、metadata 與 DPAPI。Windows 日常程式更新用 update check／apply／status，不需重佈署 Worker；舊 ZIP 接管依 WINDOWS-INSTALL-UPDATE 的 adopt 流程。不要因重新登入而重建入口或輪替 KEY。Mac／Cloud 不屬於 Windows 更新的附帶工作。

Claude／Codex 訂閱由我自行登入，不操作既有視窗、不 logout/login、不改全域設定。預設使用 Codex 做合成推論，不呼叫我正在使用的 Claude。先用 API／CLI，不重開電腦；需要 UI 驗證再列明範圍。

用專用臨時 KEY 真測 HTTPS models GET、非串流 chat POST、數值 usage.cost、撤銷，以及只重啟 Bridge 後同 URL／同 KEY 仍有效。原始 request／response 與完整 KEY 不落磁碟，僅保留 allowlist metadata。未知結果不盲目重試，依 UUID 查 receipt。測試 KEY 結束撤銷；更新驗收不能重建新 KEY 冒充舊 KEY 保留。

驗收後另建 owner 服務長效 KEY：Windows Setup 使用 byo key-create --label 'My service' --handoff；source helper 直接 key-create。新 KEY 預設兩來源全開，仍受登錄模型／訂閱限制。owner KEY 保留有效，只撤銷測試 KEY。一次性結果交 owner 放服務端 secret，不寫 repo／報告；持久聊天只提供不含 KEY 的 handoff，完整 KEY 在本機一次性介面取得。

交付固定 public_url + /api/v1、有效長效 KEY 與 integration.prompt。只承諾支援的 Chat Completions 子集：可關串流、移除抽樣／token上限；tools 是呼叫端執行的提案，不是本機工具；Responses 未支援。列出真實通過／未驗證／需要 owner 完成的登入，不能只以 HTTP 200 或 source tests 聲稱安裝交付完成。
```

工具入口：[Windows Setup／CLI](WINDOWS-INSTALL-UPDATE.md)、[source 安裝](CROSS-PLATFORM-INSTALL.md)、[完整 API](API.md)。不要將歷史報告中的網址或配對資料當成新裝置預設。
