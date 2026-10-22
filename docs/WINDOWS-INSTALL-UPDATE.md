# Windows 原生安裝與更新

此流程使用 PyInstaller onedir 與 Velopack，只有 Windows x64 internal；不改 Mac 安裝與 Cloud。暫無 Authenticode 公發憑證，作業系統仍可能提示未知發布者或依企業政策封鎖。更新政策的 Ed25519 簽章不代表 Windows 發布者簽章。

本輪 [隔離 Setup／A→B 驗收紀錄](qa/2026-10-22-windows-velopack-acceptance.md) 記錄實際安裝與資料保留；沒有測過的外網／新訂閱與乾淨 VM 不列為通過。

## 首次安裝及 CLI

執行 Setup.exe，開啟管理介面。安裝目錄中的 `current/aigo-bridge.exe` 是 console CLI；GUI 與 CLI 共用 frozen runtime，不需要 Python。首次設定使用 `aigo-bridge.exe setup`，或使用 `byo doctor`、`byo plan`、`byo deploy` 分步完成。部署仍需 Node.js 22+、Wrangler 與安裝者自己的帳戶；不自動變更 provider／Cloudflare 登入。

所有命令可帶 `--data-dir <原設定檔>`。BYO 子命令寫在 `byo` 後，例如 `aigo-bridge.exe byo status --data-dir <路徑>`。`setup` 會先 doctor，要求明確 account ID，展示計畫並確認後部署，最後可建立僅顯示一次的 Codex 服務 KEY。未完成環境／登入時，依 [BYO 指南](BYO-QUICKSTART.md) 操作；不是安裝完成即代表已有公開入口。

## 既有 ZIP 安裝接管

先 pause／wait-idle 並正常關閉舊 Bridge，再執行新 `Setup.exe --silent`，避免先以預設 profile 啟動。使用 CLI `adopt --manifest <舊 install.json> --data-dir <原 data_dir>`；資料不搬移、不重建裝置、不輪替 KEY。接著使用 `start --data-dir <同目錄>`。舊程序仍在時拒絕接管；不自動殺程序或刪除舊安裝。首次安裝／更新時勿自動啟動舊捷徑。

## 檢查及更新

`update check` 驗證固定公鑰簽署的 policy；`update apply` 再驗一次、下載並驗證完整包，排空本設定檔、備份 metadata SQLite／DPAPI、正常停止此 Bridge，交給 Velopack 套用並用相同 data-dir 重啟。`update status` 顯示重啟後完成結果。沒有 Worker 部署或訂閱登入動作。

程式啟動時與常駐期間每六小時檢查，管理介面亦可手動檢查；有更新時顯示跨頁提示，不自動安裝。GUI 背景檢查失敗不停止現有服務；已驗證最低版本限制會暫停新接單，管理功能與已完成工作的查詢仍開放，不中斷進行中的推論。重啟或之後斷網也保留已取得的限制，不能用一般「恢復接單」略過；完成更新後恢復限制前的接單設定。從未連上更新站的裝置無法得知新限制，不宣稱可離線遠端強制更新。

下載／驗證失敗發生在停止服務前；排空超時恢復原接單狀態。若套用或啟動失敗，`updates/pending.json` 與 metadata 備份保留；不要讓舊版讀取不相容 schema，也不要重播未知請求。結果只在 RAM，更新會清除 RAM 回覆，已知 token／cost receipt 仍在 metadata DB。

若原生安裝器未成功替換 A，正常停止此設定檔後可用原 CLI `update recover --data-dir <原目錄>`。它只允許原版本、原 package ID 與完全相同資料庫 schema，恢復接單設定並保留失敗紀錄；不回寫舊備份覆蓋新資料。若已換成 B 或 schema 改變，拒絕舊版恢復，改安裝更高版本修復。

更新站只提供公開版本資訊及安裝檔，不收取 provider 憑證、client KEY 或原始 request。配對憑證仍由 DPAPI 保護，KEY 僅存 hash。解除安裝預設保留外部資料目錄；清除裝置必須另外明確操作。

## 建置、渠道與驗收

`packaging/windows/release-target.json` 是 Windows 安裝包版本與身份；repo VERSION 是共用核心版本。Mac 不跟著 Windows 安裝包升版。使用 `build_installer.py`，傳入公開金鑰、HTTPS policy URL、vpk 與獨立輸出目錄；可分發包要求乾淨 commit。`sign_update.py` 只從 stdin 讀取簽署私鑰。Setup、full nupkg、feed、artifacts.json 與 self-test.json 要以同一 release set 保存，不覆寫已發布版本。

LocalProbe 使用獨立 package ID、臨時更新公鑰及明確 loopback policy；不可分發、不可宣布到 internal 渠道。`verify_installer_update.py` 真正執行 Setup、啟動 A、透過 signed policy／native Velopack 升至 B，再核對 URL、原 KEY、metadata 與 DPAPI。測試不修改 Worker，不代表外網或新訂閱授權驗收。

## Windows 專屬 CI/CD

`windows-installer.yml` 在 Windows runner 跑鎖定依賴、核心／policy 測試及真實 Setup→A→B→解除安裝，僅上傳不含 KEY 的 acceptance.json。`windows-installer-publish.yml` 只由 main 手動觸發，預設僅建置；announce=true 才宣布 Windows internal，不觸發 Mac 流程。

首次啟用發布需設定 repository variable `BRIDGE_WINDOWS_UPDATE_PUBLIC_KEY`（32-byte Ed25519 公鑰的 base64）及 windows-internal environment secret `BRIDGE_WINDOWS_UPDATE_PRIVATE_KEY`（對應 32-byte 私鑰的 base64）。這與 client KEY、DEVICE_KEY、Cloudflare 登入及 Windows 公發憑證完全不同。不從 BYO 使用者收取任何發布憑證。

更新來源使用本 repo 的 Windows 專屬固定 Release `windows-updates-internal/windows-x64-internal-policy.json`，每版產物則在 `windows-installer-internal-v<version>`，不使用通用 latest、不需新增 Cloud／Supabase 或 Pages 部署。這是靜態自建 policy 的第一版落地方式；未啟用／未宣布時，安裝程式仍可運行，更新檢查顯示來源不可達。

安裝者不需要 GitHub 登入或 PAT：更新 assets 必須可匿名 HTTPS 下載，發布器會實測。若日後將 repo 設為 private，需另選公開的專屬更新 repo／靜態儲存來源並更新安裝包設定，不能把發布 PAT 塞進安裝包。安裝者自己的 BYO Cloudflare 僅提供推論入口；Windows 更新由發布方的 GitHub Actions 簽署及發布。`version` 代表可更新版本，`minimum_version` 代表繼續接收新工作的最低版本；後者提高才會要求強制更新。

若 B 先以選用更新發布，之後才要求 A 必須更新，手動執行同一發布 workflow：`announce=true`、`published_version=B 的版號`、`minimum_version=B 的版號`。此模式重用已發布且驗證過的原始安裝包，提高 policy 序號與最低版本，不重新打包、不替換同版檔案。policy 有效期為三十天；到期前七天內可用相同模式續期。尚未接到強制政策時，來源到期／無法連線只顯示不可用，不憑空停用現有服務；已接到的最低版本限制則保留。

發布器驗證來源在 main、完整產物及固定身份，先上傳 immutable 版本並匿名下載回讀 SHA256，最後才更新 Windows pointer。只允許序號遞增，不覆寫同版內容或降低最低版本；重試相同內容可安全略過。CI 只有 Windows 渠道寫入流程，沒有 Supabase、Cloudflare 或 Mac 憑證。
