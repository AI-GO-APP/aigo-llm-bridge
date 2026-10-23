# Windows 原生安裝與更新

現行規格總入口見 [產品文件](README.md)；管理台風格與深淺色見 [設計規範](DESIGN-SYSTEM.md)，資料與備份見 [SCHEMA](SCHEMA.md)。Windows 安裝器版本以 `packaging/windows/release-target.json` 為準，不以共用核心 VERSION 的 Mac 候選標記推斷。0.7.3 的發布／正式升級狀態見 [本輪驗收](qa/2026-10-23-windows-design-docs.md)。

此流程使用 PyInstaller onedir 與 Velopack，只有 Windows x64 internal；不改 Mac 安裝與 Cloud。暫無 Authenticode 公發憑證，作業系統仍可能提示未知發布者或依企業政策封鎖。更新政策的 Ed25519 簽章不代表 Windows 發布者簽章。

前輪 [隔離 Setup／A→B 驗收紀錄](qa/2026-10-22-windows-velopack-acceptance.md) 記錄實際安裝與資料保留；沒有測過的外網／新訂閱與乾淨 VM 不列為通過。

本輪 [Windows WebView2 API／CLI 驗收](qa/2026-10-23-windows-webview-acceptance.md) 列出原生剪貼簿、CSV 與更新的實測及 UI 界線。

## 首次安裝及 CLI

0.8.0 新增 [首次安裝精靈](ONBOARDING.md)：CLI／Cloudflare 授權、明確選帳戶、一鍵或 AI IDE 部署、插電電源同意與還原、長效 KEY 及真 HTTPS cost 驗證。完成後日常啟動直接主畫面；升級保留完成紀錄及原 profile。`onboarding open/status` 可由 CLI 操作。0.8.0 internal 已發布；見 [發布收據](qa/2026-10-23-windows-080-release.md)。本輪未升級 owner 正式安裝。

執行 Setup.exe，開啟管理介面。安裝目錄中的 `current/aigo-bridge.exe` 是 console CLI；GUI 與 CLI 共用 frozen runtime，不需要 Python。首次設定使用 `aigo-bridge.exe setup`，或使用 `byo doctor`、`byo plan`、`byo deploy` 分步完成。部署仍需 Node.js 22+、Wrangler 與安裝者自己的帳戶；不自動變更 provider／Cloudflare 登入。

所有命令可帶 `--data-dir <原設定檔>`。BYO 子命令寫在 `byo` 後，例如 `aigo-bridge.exe byo status --data-dir <路徑>`。`setup` 會先 doctor，要求明確 account ID，展示計畫並確認後部署，最後可建立僅顯示一次的服務 KEY。新 KEY 預設開放 Claude／Codex 所有目前及之後登錄的模型；仍受本機模型目錄及訂閱權限限制，可明確指定 provider 縮限，既有 KEY 與輪替 scope 不變。未完成環境／登入時，依 [BYO 指南](BYO-QUICKSTART.md) 操作；不是安裝完成即代表已有公開入口。

## Windows 管理視窗

0.7.1 使用系統 Evergreen WebView2 與 pywebview 薄外殼，不隨包附 Chromium。共用 HTML／JS 透過 `BridgePlatform` 呼叫平台適配層；Windows 才附加原生剪貼簿與 CSV 儲存對話框，瀏覽器保留自己的剪貼簿／下載流程。Mac 封裝及驗收獨立。

管理視窗是獨立程序，關窗仍保留背景服務；再次開啟會還原同一視窗。更新先排空並關閉本設定檔的服務及視窗，再套用版本。缺少 WebView2、視窗載入失敗或程序異常退出會開啟預設瀏覽器，頁首亦可手動切換；可用 GUI 的 `--browser` 明確選擇。瀏覽器 session token 只在記憶體與 URL fragment，不放入命令列。

LocalProbe 的 `--console-probe` 只在不可分發包啟用，以隱藏的實際 WebView2 renderer 驗證 KEY 複製、同 KEY HTTP 認證、CSV 中繼資料與關窗常駐，不操作桌面。CSV 測試由測試程式供應 Save 對話框的選擇結果；它驗證前端→原生 bridge→管理 API→檔案，但不代表人工點選系統儲存對話框或視覺排版驗收。

## 既有 ZIP 安裝接管

先 pause／wait-idle 並正常關閉舊 Bridge，再執行新 `Setup.exe --silent`，避免先以預設 profile 啟動。使用 CLI `adopt --manifest <舊 install.json> --data-dir <原 data_dir>`；資料不搬移、不重建裝置、不輪替 KEY。接著使用 `start --data-dir <同目錄>`。舊程序仍在時拒絕接管；不自動殺程序或刪除舊安裝。首次安裝／更新時勿自動啟動舊捷徑。

## 檢查及更新

`update check` 驗證固定公鑰簽署的 policy；`update apply` 再驗一次、下載並驗證完整包，排空本設定檔、備份 metadata SQLite／DPAPI、正常停止此 Bridge，交給 Velopack 套用並用相同 data-dir 重啟。`update status` 顯示重啟後完成結果。沒有 Worker 部署或訂閱登入動作。

0.7.2 修正固定 GitHub Release 網址必須使用 Velopack `HttpSource` 的問題。0.7.0／0.7.1 的檢查可正常顯示新版，但直接套用 GitHub 更新會因 SDK 自動選擇儲存庫來源而失敗，服務與資料不會被停止或清除。這兩版需先正常停止 Bridge，以新版 Setup 在同一原生安裝目錄升級並沿用原 data-dir；既有版本檔案不覆寫。之後使用 0.7.2 的正常簽章更新流程。

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
