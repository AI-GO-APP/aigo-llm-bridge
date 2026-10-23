# 自有 Cloudflare 安裝指南

Windows 0.8.0 候選可透過 [首次安裝精靈](ONBOARDING.md) 執行官方 CLI 授權、明確選帳戶、一鍵部署或複製 AI IDE 協作 prompt。首次本人電源同意、KEY 保存及真 HTTPS／cost 測試完成後，日常啟動直接主畫面；此段不是宣稱候選已發布，實際狀態見 QA。

Windows 新安裝優先使用 [PyInstaller＋Velopack Setup](WINDOWS-INSTALL-UPDATE.md)，不需要 Python；原始碼安裝見 [repo 流程](CROSS-PLATFORM-INSTALL.md)。舊 ZIP 路線保留在下方，不能和 Setup 共用程式目錄。Mac 由其維護者獨立驗收與發布。產品正本見 [文件入口](README.md)；完成後交付 [第三方串接訊息](THIRD-PARTY-INTEGRATION.md)、固定 endpoint 與可用長效 KEY。

適合進階使用者與其 AI agent。每個安裝者自己擁有 Worker、Cloudflare 帳單、裝置設定與登入。發布方只提供程式，不管理任何安裝者的入口或帳戶。沒有中央註冊、共享 API key 或預設公開 endpoint。

## 準備

- 安裝 Windows 版，或取得完整 repo、安裝 `desktop_bridge/requirements.txt`。
- 安裝 Node.js 與 Wrangler，例如 `npm.cmd install -g wrangler@4.95.0`。可指定 `--wrangler-js <完整JS入口>`；執行採 Node 原生入口，不以 shell 插入參數。
- 使用自己的 `wrangler.cmd login` 完成官方授權，再用 `wrangler.cmd whoami` 在本機查看目標帳戶。不要把 token、Global API key 或 `auth.json` 提供給發布方／聊天。
- 全新 Cloudflare 帳戶還需完成免費 workers.dev 子網域的首次選名。若自動 deploy 失敗且帳戶從未啟用 Workers，先完成下方 plan，再於互動終端執行 `wrangler.cmd deploy --config (Join-Path $data 'byo-worker\wrangler.json')`，讓 Wrangler 官方提示註冊該帳戶的 workers.dev 子網域，再回來執行 `& $setup deploy --data-dir $data` 配對。不要改用臨時網址、其他人的帳戶或刪除原裝置資料；子網域選定後不要任意更名。BYO helper 的非互動部署不代答帳戶註冊問答。
- Windows 指令使用 npm.cmd／wrangler.cmd，避免 PowerShell 把同名 .ps1 擋下；不需改全域 ExecutionPolicy。
- 由使用者在 Claude Code／Codex 登入自己的訂閱。Bridge 不代登入或登出正在使用的 CLI。

## Windows Setup：目前建議路線

從本 repo 的 Windows installer internal Release 下載 Setup，完成安裝後在實際安裝目錄的 `current` 開啟 PowerShell；此目錄有 `aigo-bridge.exe`。先確認輸出版本／package ID，不把解壓暫存路徑當永久安裝路徑。

```powershell
$cli = (Resolve-Path '.\aigo-bridge.exe').Path
& $cli version
& $cli setup
# setup 會 doctor、確認自己的 account、plan、明確確認 deploy，並可一次性建立服務 KEY。
& $cli byo status
& $cli start
```

也可用 `& $cli byo doctor`／`byo plan --account-id ...`／`byo deploy` 分步執行；需要自訂 profile 時每次帶相同 `--data-dir`。KEY 與 handoff 的命令都是 `byo key-create`／`byo handoff`。完整 KEY 不可寫檔／argv／報告。更新使用 `& $cli update check`、`update apply`、`update status`，保留原 data-dir；**日常 Windows 程式更新不需要重新 deploy Worker**。詳見 [安裝及更新](WINDOWS-INSTALL-UPDATE.md)。

## 舊 ZIP：不使用 Python 的 CLI 路線

以下僅供既有 ZIP 安裝；新版 Setup 請用上一節，不執行 Install.ps1。

解壓 ZIP，進入內層 `AIGO-LLM-Bridge-BYO`（包含 Install.ps1 的目錄），在 PowerShell 執行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Install.ps1
$install = Get-Content "$env:LOCALAPPDATA\AIGO LLM Bridge\install.json" -Raw | ConvertFrom-Json
$app = Split-Path $install.exe
$setup = Join-Path $app 'BYO-Setup\AIGO-Bridge-Setup.exe'
$data = $install.data_dir
& $setup status --data-dir $data
wrangler.cmd whoami
# 用自己帳戶的真實 ID；不要把尖括號範例直接貼入 PowerShell。
$account = Read-Host '自己的 Cloudflare account ID'
& $setup plan --data-dir $data --account-id $account
& $setup deploy --data-dir $data
$created = & $setup key-create --data-dir $data --label 'My web service' | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Key creation failed' }
# created.key 是只顯示一次的長效 key；程式只存 hash，不寫明文檔。
Start-Process -FilePath $install.exe -ArgumentList ('--headless --data-dir "' + $data + '"') -WindowStyle Hidden
$status = & $setup status --data-dir $data | ConvertFrom-Json
$headers = @{ Authorization = 'Bearer ' + $created.key }
# 首次 agent poll 最多約 20 秒；若剛建立 key 暫回 401，稍等重試。
Invoke-RestMethod ($status.public_url + '/health')
Invoke-RestMethod ($status.public_url + '/api/v1/models') -Headers $headers
$body = @{model='openai/gpt-6-astra'; messages=@(@{role='user';content='Reply OK.'}); stream=$false} | ConvertTo-Json -Depth 8
Invoke-RestMethod ($status.public_url + '/api/v1/chat/completions') -Method Post -ContentType 'application/json' -Headers $headers -Body $body
```

`key-list` 只列 ID／前綴／權限，不含明文；`key-rotate --key-id <ID>` 回傳新的 key 並立即撤銷舊 key；`key-revoke --key-id <ID>` 可重複執行。安裝驗證使用臨時 key，完成後撤銷：`& $setup key-revoke --data-dir $data --key-id $created.id`。不要將明文 key 寫入驗收報告、prompt、命令列參數或檔案。管理 UI 也可做相同操作。

自訂／隔離安裝可執行 `.\Install.ps1 -InstallRoot 'D:\Bridge' -DataDir 'D:\BridgeData'`；可加 `-NoShortcuts`，或 `-ShortcutDirectory 'D:\BridgeShortcuts'` 將捷徑放到指定資料夾。捷徑綁定相同 data-dir。未帶 `-Launch` 不啟動程式，未帶 `-AutoStart` 不新增開機登入啟動。

更新時先讓 Bridge 排空（pause／wait-idle），只關閉該 Bridge；解壓新版，再以**同一 InstallRoot** 執行 Install.ps1，不必再指定 DataDir（從 install.json 沿用）。安裝器拒絕將已存在的安裝改指另一 DataDir。更新保留資料與舊版本，捷徑指向新版本；若原安裝已設開機啟動，也會更新其路徑。需自行重新啟動 Bridge；安裝不會中止其他程式。每次更新後重新讀 install.json，避免操作舊版本的 setup CLI。

## 初次部署（原始碼）

下例是在 repo 執行；解壓安裝包先進入 `app`，已安裝則進版本目錄，再將 `python tools/byo_setup.py` 換成 `BYO-Setup\AIGO-Bridge-Setup.exe`。預設資料目錄是 `%LOCALAPPDATA%\AIGO LLM Bridge\data`，若原本有自訂目錄，每個指令都帶相同 `--data-dir`。

```powershell
python tools/byo_setup.py status
python tools/byo_setup.py plan --account-id <你自己的32字元Cloudflare-account-id>
python tools/byo_setup.py deploy
```

`plan` 僅生成本機專案與綁定，不部署。它使用裝置 UUID 產生固定 `llm-bridge-...` Worker 名稱，將原始碼與含 account_id 的 `wrangler.json` 放到資料目錄的 `byo-worker/`。**不要直接部署 repo 的 wrangler.jsonc 範本**，也不要把生成的個人 config 提交 Git。

`deploy` 先核對目前 CLI 可管理原綁定帳戶，再部署並配對 DEVICE_KEY。配對 secret 經 stdin 傳入 Wrangler，不進 argv 或明文檔；本機只存 DPAPI。重跑沿用同一裝置、Worker、URL、client API key，不重新分配身分。失敗時保留加密 pending 憑證供重試，不要自行刪除裝置資料來重做。

若已有自己部署的專屬 Bridge Worker，首次 plan 時指定它的原名稱（或直接 pair 帶 account-id／url 自動採用原名稱），例如：

```powershell
python tools/byo_setup.py plan --account-id <自己的account-id> --worker-name your-worker
python tools/byo_setup.py pair --url https://your-worker.your-subdomain.workers.dev
```

啟動 Bridge（開啟桌面捷徑或 `python -m desktop_bridge`），在管理頁建立自己的長效 API key。Base URL 為你自己的 Worker URL 加 `/api/v1`。Node／Wrangler 只用於部署管理，正常 relay 運行不需要其 Cloudflare 部署權限；發布方無法替你恢復或撤銷入口。

每個 Worker 目前只配一個裝置設定檔。同一裝置的 Claude／Codex 共用入口，用 model 與 key scope 區分。另一台裝置預設產生另一個 UUID／Worker；不複製配對給同時在線的兩台電腦。

pair／repair 會重新部署隨附 Bridge 範本，先核對該帳戶實際回報的 workers.dev 網址，再設定 secret；不將裝置憑證送往任意指定 URL。自訂網域需要另行核對 Cloudflare 路由，工具不自動配對。

## 切換訂閱登入

```powershell
python tools/byo_setup.py pause
python tools/byo_setup.py wait-idle --timeout 180
# 使用者自行切換 Claude Code／Codex 登入，再唯讀檢查 auth/login status
python tools/byo_setup.py resume
```

這些命令不修改 endpoint、device_id 或 API key。`pause` 不會中止已排隊／執行中的工作；等 wait-idle 成功才換帳號。已有 client key 的服務會使用之後登入的訂閱，若不希望它們繼續使用，另行撤銷／輪替 key。不要用一次切換承諾同時服務兩個同供應商帳戶；那需要已隔離的 CLI 登入環境，目前未自動化。

## 恢復與更新

保留資料目錄及原 Worker 名稱，重新部署同一計畫即可更新 Worker；更新 Bridge 安裝版本也保留資料。Cloudflare 登入過期時只在下一次部署管理重新授權，日常 relay 使用獨立裝置 key，不會因此改網址。帳戶錯誤時工具停止，不自動搬到新帳戶。

Windows 使用者更換／重灌：經授權恢復原裝置 DB 後，先登入原 Cloudflare owner，再以 `repair-device-key` 重新配對；這只輪替 transport secret，保留 DB 內 API key hash、device_id、原 URL。請先停止舊 Bridge，並在新 Windows 使用者自己登入供應商 CLI。詳見 [身分與授權表](DEVICE-IDENTITY.md)。沒有原 DB／備份就無法還原原 key hash；沒有 Cloudflare owner 權限就不能恢復原 Worker。

## 驗證與限制

必查 HTTPS `/health`、帶 key 的 models GET、合成 chat POST、撤銷回 401、程式重啟後原 URL／key。不要使用真實客戶 prompt 作安裝驗證。`tools/p1_manage_acceptance.py` 是已有安裝的開發驗收腳本，會管理其專用測試 key 並只重啟 Bridge；不是必要的初次部署步驟。

外部仍採 POST／GET，支援與限制見 [P1 相容範圍](P1-Windows-guide.md)。沒有自有網域也可用固定 workers.dev，前提是保留 account subdomain 與 Worker 名稱；刪除 Worker、改 subdomain 或移動 Cloudflare 帳戶可能改網址。免費方案有共享的帳戶用量上限，長輪詢仍有 DO 活動時間消耗；安裝者自行監控額度。方案升級與網域購買不會自動執行。

官方：[Wrangler 命令](https://developers.cloudflare.com/workers/wrangler/commands/)、[Secrets](https://developers.cloudflare.com/workers/configuration/secrets/)、[workers.dev](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)、[DO 計價](https://developers.cloudflare.com/durable-objects/platform/pricing/)。

API 診斷：若 Cloudflare 直接回 HTML／文字 403、1010，而非 Bridge JSON，先檢查客戶端 User-Agent 與自己帳戶的安全規則；不要更換 KEY 或重建 Worker。Python urllib 測試請明確標示 User-Agent（例如 `aigo-llm-bridge-client/1.0`），並使用有效 CA 憑證；不要關閉 TLS 驗證。本機 relay 已內建 User-Agent 與 CA bundle。[Cloudflare 1010 說明](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)。

新 KEY 預設允許 Claude／Codex 所有已登錄模型，之後新增模型不需重發 KEY。仍須符合本機訂閱與模型目錄；需要限制時明確傳入 `--providers codex` 或 `--providers claude`。既有 KEY 及其輪替範圍不會自動擴權。
