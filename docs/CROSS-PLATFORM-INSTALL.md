# 從 repo 安裝：Windows / macOS

本流程供進階使用者與其 AI agent 使用。Windows 亦可使用不需 Python 的原生 ZIP；macOS 目前提供原始碼安裝器，尚未提供原生 .app／DMG。macOS 是否已實機驗收須以最新驗收報告為準，不能用 Windows 測試或 CI 設定取代。

## 前置條件

- Python 3.12+（含 venv/pip）、Node.js 22+、網路，以及安裝者自己的 Cloudflare 帳戶。
- 安裝 Wrangler：Windows `npm.cmd install -g wrangler@4.95.0`；macOS `npm install -g wrangler@4.95.0`。若沒有全域安裝權限，可在 repo 的 cloudflare 目錄安裝相同版本，helper 會找本機 node_modules。
- 安裝者自行完成 `wrangler login`、`wrangler whoami`。Windows 使用 `wrangler.cmd`。全新帳戶還需依官方互動提示註冊 workers.dev 子網域；部署不需要購買網域，亦不會代為升級帳單方案。
- 安裝者自行安裝 Codex CLI，並以自己的 ChatGPT 訂閱登入；預設串接示範選擇 Codex 模型。Claude 是選用來源；不要登出、切換或操作已在使用的 Claude Code。`doctor` 只讀取登入狀態。
- macOS 的登入鑰匙圈需要可用；首次存取可能顯示系統授權提示，由使用者處理。SSH 的未解鎖 Keychain 不能視為可完成首次部署。程式不改用明文檔繞過此限制。

## 原始碼安裝

在 repo 根目錄執行 Windows `python tools/install.py`，或 macOS `python3 tools/install.py`。它會建立專用 venv、安裝鎖定依賴、複製程式及部署指南，輸出不含憑證的 JSON 安裝資訊。不需要 sudo，不改 provider 的全域設定或登入，也不會自動啟動瀏覽器。

Windows 預設為 `%LOCALAPPDATA%\AIGO LLM Bridge Source`，與既有原生 ZIP 安裝隔離。macOS 預設為 `~/Library/Application Support/AIGO LLM Bridge`。兩者資料都在該安裝目錄的 `data`，詳見 `source-install.json`。

可帶 `--install-root <路徑>`、`--data-dir <路徑>` 做隔離安裝。更新時以同一 install-root 重跑，沿用資料、UUID、Worker URL 與 key hash；拒絕改指別的 data-dir。舊版本保留。更新前暫停、排空並關閉**此安裝**的 Bridge，更新不會自動停止任何程序。不要把原生 ZIP 安裝目錄交給此 source 安裝器。

## macOS CLI 完整範例

```sh
python3 tools/install.py
export BRIDGE_ROOT="$HOME/Library/Application Support/AIGO LLM Bridge"
# 完成安裝後讀安裝資訊；python/app/data 以實際 source-install.json 為準。
export BRIDGE_PY="$BRIDGE_ROOT/runtime/bin/python"
export BRIDGE_DATA="$BRIDGE_ROOT/data"
export BRIDGE_APP="$("$BRIDGE_PY" -c 'import json,os; print(json.load(open(os.path.join(os.environ["BRIDGE_ROOT"],"source-install.json")))["app"])')"
"$BRIDGE_PY" "$BRIDGE_APP/tools/byo_setup.py" doctor --data-dir "$BRIDGE_DATA"
wrangler whoami
# 下面由安裝者填入自己的 account ID，不能使用報告或範本中的其他人帳戶。
printf 'Cloudflare account ID: '; read -r BRIDGE_ACCOUNT
"$BRIDGE_PY" "$BRIDGE_APP/tools/byo_setup.py" plan --data-dir "$BRIDGE_DATA" --account-id "$BRIDGE_ACCOUNT"
"$BRIDGE_PY" "$BRIDGE_APP/tools/byo_setup.py" deploy --data-dir "$BRIDGE_DATA"
"$BRIDGE_PY" "$BRIDGE_APP/tools/byo_setup.py" key-create --data-dir "$BRIDGE_DATA" --label 'My web service' --providers codex --handoff
"$BRIDGE_ROOT/Bridge.command"
```

上述指令可用 Bash / zsh。`key-create --handoff` 的一次性輸出含 key；只交給擁有者／受信任的串接端，勿以 `tee` 或重導寫檔、勿放進驗收報告。安裝 agent 應將這份輸出保留在記憶體，交由使用者放入服務端 secret。

全新 Cloudflare 帳戶若尚無 workers.dev，plan 完成後先在互動終端執行 `wrangler deploy --config "$BRIDGE_DATA/byo-worker/wrangler.json"` 完成選名，再回 helper deploy 配對。此時仍須核對自己的 account ID。不要直接部署 repo 範本。

需要不開管理頁的驗收可用 `"$BRIDGE_ROOT/Bridge.command" --headless --port <隔離連接埠>`；正常啟動會開啟本機 Web Console。macOS 勾選登入啟動時寫入此 profile 專屬 LaunchAgent，**下次登入生效**，不是開機未登入就可服務；停用也於下次登入生效。Python 路徑或使用者帳號變更需重新設定啟動項。

## Windows repo 安裝後的 CLI

```powershell
python tools/install.py
$m = Get-Content "$env:LOCALAPPDATA\AIGO LLM Bridge Source\source-install.json" -Raw | ConvertFrom-Json
$setup = Join-Path $m.app 'tools\byo_setup.py'
& $m.python $setup doctor --data-dir $m.data_dir
wrangler.cmd whoami
$account = Read-Host '自己的 Cloudflare account ID'
& $m.python $setup plan --data-dir $m.data_dir --account-id $account
& $m.python $setup deploy --data-dir $m.data_dir
$created = & $m.python $setup key-create --data-dir $m.data_dir --label 'My web service' --providers codex --handoff | ConvertFrom-Json
# 一次性含 key 的標準訊息：只複製給受信任的服務端 IDE，不寫入檔案。
$created.integration.prompt | Set-Clipboard
& $m.python $m.launcher
```

要取得不含 key 的串接說明：`handoff --data-dir ... --providers codex`。`status` 回報 URL／配對狀態，`key-list` 僅回傳前綴及 ID；不提供舊明文 key 的查回功能。模型由 GET models 決定，需與本機訂閱權限、CLI 模型及 OpenRouter 牌價相符。

最後必須完成 [第三方串接驗收](THIRD-PARTY-INTEGRATION.md)。安裝、Cloudflare 部署與真實訂閱推論各是獨立檢查；登入或 Keychain 不可用時明確回報未完成。

macOS 儲存與啟動依據：[Apple Keychain](https://developer.apple.com/documentation/security/seckeychainfindgenericpassword(_:_:_:_:_:_:_:_:))、[Apple LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)。
