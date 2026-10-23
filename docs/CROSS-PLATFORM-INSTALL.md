# 從 repo 安裝：Windows / macOS

本流程供進階使用者與其 AI agent 使用。Windows 新安裝優先使用不需 Python 的 [Velopack Setup](WINDOWS-INSTALL-UPDATE.md)，舊原生 ZIP 為另一條安裝路徑；macOS 提供 [Mac Release source ZIP](MACOS-RELEASE.md)，下載後驗 SHA256、解壓、執行 Install.command 或下方 Python 指令；尚未提供公證 .app／DMG。macOS 是否已實機驗收須以最新驗收報告為準，不能用 Windows 測試或 CI 設定取代。

## 前置條件

Mac `0.9.1-mac.1` 的 WKWebView、五步精靈及來源更新見 [Mac 操作契約](MACOS-SETUP.md)。關閉視窗仍在背景接單；安裝不自動更改電源或啟動 OAuth。

- Python 3.12+（含 venv/pip）、Node.js 24.22.1+（或 22.23.4+）、網路，以及安裝者自己的 Cloudflare 帳戶。
- 安裝 Wrangler：Windows `npm.cmd install -g wrangler@4.152.0`；macOS `npm install -g wrangler@4.152.0`。若沒有全域安裝權限，可在 repo 的 cloudflare 目錄安裝相同版本，helper 會找本機 node_modules。
- 安裝者自行完成 `wrangler login`、`wrangler whoami`。Windows 使用 `wrangler.cmd`。全新帳戶還需依官方互動提示註冊 workers.dev 子網域；部署不需要購買網域，亦不會代為升級帳單方案。
- 安裝者自行安裝 Codex CLI，並以自己的 ChatGPT 訂閱登入；預設串接示範選擇 Codex 模型。Claude 是選用來源；不要登出、切換或操作已在使用的 Claude Code。`doctor` 只讀取登入狀態。
- macOS 的登入鑰匙圈需要可用；首次存取可能顯示系統授權提示，由使用者處理。SSH 的未解鎖 Keychain 不能視為可完成首次部署。程式不改用明文檔繞過此限制。

## 原始碼安裝

在 repo 根目錄執行 Windows `python tools/install.py`，或 macOS `python3 tools/install.py`。它會建立專用 venv、安裝鎖定依賴、複製程式及部署指南，輸出不含憑證的 JSON 安裝資訊。不需要 sudo，不改 provider 的全域設定或登入，也不會自動啟動瀏覽器。

Windows 預設為 `%LOCALAPPDATA%\AIGO LLM Bridge Source`，與既有原生 ZIP 安裝隔離。macOS 預設為 `~/Library/Application Support/AIGO LLM Bridge`。兩者資料都在該安裝目錄的 `data`，詳見 `source-install.json`。

可帶 `--install-root <路徑>`、`--data-dir <路徑>` 選擇安裝與資料位置。Mac 同一台電腦僅允許一個 runtime，不因另選目錄／API port 而允許雙開。更新時以同一 install-root 重跑，沿用資料、UUID、Worker URL 與 key hash；拒絕改指別的 data-dir。舊版本保留。更新前暫停、排空並關閉**此安裝**的 Bridge，更新不會自動停止任何程序。不要把原生 ZIP 安裝目錄交給此 source 安裝器。

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
"$BRIDGE_PY" "$BRIDGE_APP/tools/byo_setup.py" key-create --data-dir "$BRIDGE_DATA" --label 'My web service' --handoff
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
$created = & $m.python $setup key-create --data-dir $m.data_dir --label 'My web service' --handoff | ConvertFrom-Json
# 一次性含 key 的標準訊息：只複製給受信任的服務端 IDE，不寫入檔案。
$created.integration.prompt | Set-Clipboard
& $m.python $m.launcher
```

要取得不含 key 的串接說明：`handoff --data-dir ... --providers codex`。`status` 回報 URL／配對狀態，`key-list` 僅回傳前綴及 ID；不提供舊明文 key 的查回功能。模型由 GET models 決定，需與本機訂閱權限、CLI 模型及 OpenRouter 牌價相符。

模型與 Jev 使用端另依 [模型查詢與 Decisions](JEV-COMPATIBILITY.md)驗證，交付的 handoff 已包含兩種格式。新路徑需更新 Worker、Relay 與 Bridge；若本次不部署，記錄外部驗收待完成。

最後必須完成 [第三方串接驗收](THIRD-PARTY-INTEGRATION.md)。安裝、Cloudflare 部署與真實訂閱推論各是獨立檢查；登入或 Keychain 不可用時明確回報未完成。

若下一階段要以新Mac取代現有Windows作為Cloud常駐供應端，依[供應裝置交接](AI-EA-CLOUD-BEST-PRACTICE.md#下一階段改用另一台-mac-作常駐供應端)先建獨立profile並驗外部HTTPS、模型／成本、工具與錯誤，再切Cloud registry。保留原Windows URL／key作回退；本段不是Mac實機驗收或Mac release。

macOS 儲存與啟動依據：[Apple Keychain](https://developer.apple.com/documentation/security/seckeychainfindgenericpassword(_:_:_:_:_:_:_:_:))、[Apple LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)。


## macOS LaunchAgent 管理與回復

完成 source 安裝後，可使用安裝內的 `tools/mac_service.py` 管理此 profile。此工具不操作其他 CLI 視窗、不更改供應商登入；`stop`／`restart`／`rollback` 先 pause、wait-idle，再停止此 profile 的 LaunchAgent。若另有手動啟動的 Bridge 仍持有 lock，拒絕更新，不強制殺程序。

```sh
BRIDGE_ROOT="$HOME/Library/Application Support/AIGO LLM Bridge"
BRIDGE_PY="$BRIDGE_ROOT/runtime/bin/python"
BRIDGE_APP="$("$BRIDGE_PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["app"])' "$BRIDGE_ROOT/source-install.json")"
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" status
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" restart
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" stop
# 在 source checkout 用 Python 3.12+ 執行，沿用同一 root/data：
python3 tools/install.py --install-root "$BRIDGE_ROOT"
# 更新後重新從 source-install.json 讀取 BRIDGE_APP，再 start。
```

`enable`／`disable` 控制登入啟動項；`start` 會立即 bootstrap 並啟用登入啟動，`stop` 停止目前服務並暫停接單，但保留登入啟動檔。再次 `start` 會 resume。LaunchAgent 使用穩定的 `Bridge.pyw` 讀取 manifest；每個 profile 有獨立 label，正常結束不自動重啟，異常退出由 launchd 重啟。stdout/stderr 指向 `/dev/null`，不保存 CLI 原始內容。

更新保留 `source-install.previous.json` 與舊 app 目錄。使用目前安裝的 `mac_service.py rollback` 可先排空、切回上一個 manifest 再啟動，資料目錄不變；回復程式版本不回復／刪除裝置 DB。runtime 為同一 venv，若未來版本改變不相容的依賴，需按舊版 requirements 恢復依賴後再啟動。`source_commit` 記錄安裝來源的 Git commit；從有未提交變更的 checkout 安裝時仍應另核對 Git diff。

LaunchAgent 僅在該使用者登入後供應服務。休眠／關機或登入 Keychain 不可用時不能持續推論；不自動更改全機休眠、安全或登入設定。日常使用以 owner 可讀寫的 data 目錄（0700）、SQLite（0600）保存 metadata；配對 secret 只進 Keychain，無明文 fallback。完整 service KEY 由本機一次性管理視窗交付，不進一般報告。

Mac 可用 `"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_key_handoff.py"` 建立 Codex scope 的 Cloud 專用長效 KEY。本機原生一次性視窗可選擇複製 KEY 或完整串接訊息；明文由 stdin 傳給系統視窗，不進 argv、stdout、腳本檔或報告。視窗關閉後不能查回；即使取消視窗也保留該 key 有效，需用 key-list 核對後明確撤銷／輪替，不要重複產生未知用途的 KEY。此工具不替你將 KEY 注入 Cloud secret，也不修改 registry。

### Mac 同時請求與排隊

Mac source 0.9.4-mac.1 整合 [64 併發規格](CONCURRENCY.md)。新 profile 預設 64，Claude／Codex、Chat／Decisions 共用；Relay 另保留控制容量。既有 profile 更新保留原 inference_workers；管理者明確切換時執行：

```sh
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" workers --count 64 --install-root "$BRIDGE_ROOT"
```

指令先 pause／wait-idle、停止此 Bridge，再設為 1–64 並啟動原 LaunchAgent。URL、device ID、既有 Key 與 RPM 不變，數值跨更新保留。新 Key 預設 600 RPM；既有較低 RPM 仍可能回 429。同步並行 POST 即可，不需工單輪詢；超時不自動重送，先查 UUID 收據。64 是設定容量，不保證延遲或訂閱吞吐；Mac 本輪只做少量合成 HTTPS 跑通，未做真實 64 負載。

0.9.5-mac.1 起，macOS LaunchAgent 預設檔案描述符軟上限 256 會使 64 組 CLI pipe 與 API／Relay socket 耗盡描述符（實測約 40／64 可執行，其餘回 500）。Bridge 啟動時只將本程序軟上限提高到 4096（不超過硬上限），不改 launchctl 或系統設定。公開 HTTPS 的 64 名額另需原地更新同一 Worker。

增加同時推論可減少短請求被長工作阻塞，但不保證任意負載或輸出均在舊 client 的 60 秒期限內完成；訂閱限額、模型服務延遲與休眠仍可能使請求失敗。不以自動重試或未核實的零成本掩蓋失敗。
