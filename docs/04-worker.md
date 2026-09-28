# 04 · 在自己的電腦上安裝 worker

worker 讓 app 可以用「你電腦上、你自己登入的 Claude Code」處理「你自己」送出的工作。
它是一個 Python 檔,只用標準函式庫,不需要 `pip install`。**它只會領到你本人的工單**(docs/02)。

## 1. 需要什麼

| 項目 | 怎麼確認 |
|---|---|
| Python 3.9 以上 | `python --version`(macOS / Linux 可能是 `python3`) |
| Claude Code,並用**你自己的帳號**互動登入過 | 執行一次 `claude`,完成登入;`claude auth status` 應顯示已登入 |
| 能連到 Bridge 的網路 | 只需要對外 HTTPS;**電腦不用開任何對內的 port** |

不支援:以 `CLAUDE_CODE_OAUTH_TOKEN` 長效 token 執行(worker 偵測到會拒絕啟動),
以及裝在伺服器、容器、CI 上替別人跑(那不是「本人的電腦」)。

## 2. 綁定(一次)

1. 在 app 裡打開「連接我的電腦」,按「產生綁定碼」。碼 10 分鐘內有效、只能用一次。
2. 下載 worker,放在 `~/.aigo-llm-bridge/`(開機自動啟動的範本預設就找這個位置)。
   網址永遠指向最新發布的版本;要固定版本,把 `latest/download` 換成 `download/vX.Y.Z`。

   macOS / Linux:

   ```bash
   mkdir -p ~/.aigo-llm-bridge && cd ~/.aigo-llm-bridge
   curl -fsSLO https://github.com/AI-GO-APP/aigo-llm-bridge/releases/latest/download/aigo_bridge_worker.py
   ```

   Windows(PowerShell):

   ```powershell
   New-Item -ItemType Directory -Force "$env:USERPROFILE\.aigo-llm-bridge" | Out-Null; Set-Location "$env:USERPROFILE\.aigo-llm-bridge"
   Invoke-WebRequest https://github.com/AI-GO-APP/aigo-llm-bridge/releases/latest/download/aigo_bridge_worker.py -OutFile aigo_bridge_worker.py
   ```

   也可以直接從 [Releases](https://github.com/AI-GO-APP/aigo-llm-bridge/releases) 頁面下載,或用 repo 裡的
   [`worker/aigo_bridge_worker.py`](../worker/aigo_bridge_worker.py)。**只從這兩個地方取得**,不要用別人轉傳的檔案。
3. 在 `~/.aigo-llm-bridge/` 執行畫面上給的指令:

```bash
python aigo_bridge_worker.py enroll --bridge https://<your-bridge>.deploy.ai-go.app --code ABCD-EFGH
```

成功會顯示「綁定完成」,設備鑰匙存在 `~/.aigo-llm-bridge/worker.json`(只有你讀得到)。
回到 app 按「重新整理」,應該看到這台電腦。

## 3. 執行

```bash
python aigo_bridge_worker.py run       # 前景執行,Ctrl+C 結束
python aigo_bridge_worker.py status    # 檢查設定與 Claude Code 登入狀態
```

執行中 app 會顯示「在線」。每次處理工作會印一行開始與完成(或失敗原因),不會印出提示內容。

## 4. 開機自動啟動

範本在 [`worker/autostart/`](../worker/autostart),每一版的 Release 也附上同名檔案
(下載網址同 §2,把檔名換掉)。三種都是「登入後自動啟動、異常結束 1 分鐘後重啟」;
**被撤銷時 worker 以結束碼 0 正常結束,不會被無限重啟**。

| 系統 | 範本 | 安裝 |
|---|---|---|
| Windows | `install-windows-task.ps1`(工作排程器,只為目前使用者) | 在 repo 裡:`powershell -ExecutionPolicy Bypass -File worker\autostart\install-windows-task.ps1`;單獨下載的話加 `-Worker "$env:USERPROFILE\.aigo-llm-bridge\aigo_bridge_worker.py"` |
| macOS | `com.aigo.llm-bridge-worker.plist`(launchd 使用者代理) | 改檔內三個路徑 → 複製到 `~/Library/LaunchAgents/` → `launchctl bootstrap gui/$(id -u) <plist>` |
| Linux | `aigo-llm-bridge-worker.service`(systemd 使用者服務) | 複製到 `~/.config/systemd/user/` → `systemctl --user enable --now aigo-llm-bridge-worker` |

開機常駐時 PATH 常常找不到 `claude`,所以範本都設了 `AIGO_BRIDGE_CLAUDE`(Windows 安裝腳本會自動找)。
紀錄檔在 `~/.aigo-llm-bridge/worker.log`(Linux 用 `journalctl --user -u aigo-llm-bridge-worker`)。

## 5. 撤銷、換電腦、更新、移除

- **更新**:用 §2 同一個指令重新下載蓋掉舊檔,再重啟(前景執行的按 Ctrl+C 後重跑;開機常駐的重新登入或重啟服務)。
  綁定不受影響。舊版 worker 通常仍可運作,除非 [CHANGELOG](../CHANGELOG.md) 另有說明;目前版本看 `status` 的 `worker_version`。

- **撤銷**:在 app「連接我的電腦」按「撤銷」。那台電腦的 worker 下一次輪詢就收到 401 並自行結束。
- **換電腦**:在新電腦重新綁定即可。可以同時綁多台,工作由先來領的那一台處理;不用的那台記得撤銷。
- **移除**:撤銷後刪掉 `~/.aigo-llm-bridge/`,並移除開機常駐
  (Windows 加 `-Uninstall` 再跑一次安裝腳本;macOS `launchctl bootout`;Linux `systemctl --user disable --now`)。

## 6. 環境變數(都是選填)

| 變數 | 預設 | 用途 |
|---|---|---|
| `AIGO_BRIDGE_WORKER_HOME` | `~/.aigo-llm-bridge` | 設定、對話紀錄與執行目錄放哪裡 |
| `AIGO_BRIDGE_CLAUDE` | 從 PATH 找 | `claude` 執行檔的完整路徑 |
| `AIGO_BRIDGE_JOB_TIMEOUT_S` | `1800` | 單一工作的上限;超過會中止並回報失敗(不會交出半截內容) |

## 7. 它在你的電腦上做了什麼

- 每 25 秒以 HTTPS 向 Bridge 詢問「有沒有我的工作」,每 30 秒回報一次心跳。
- 有工作時,在**專用的空目錄** `~/.aigo-llm-bridge/run/` 執行 `claude -p`,**不給任何工具**
  (不能讀寫檔案、不能執行指令),只產生文字。
- 輸出送回前,把你的帳號 email、同網域的其他 email、本機路徑換成 `[redacted]`
  (Claude Code 每一輪都會附上這些環境資訊,沒有設定能關掉)。
- 不讀取、不複製、不轉送你的 Claude 登入憑證;只以子行程呼叫 `claude`。

## 8. 常見狀況

| 症狀 | 原因與處理 |
|---|---|
| `enroll` 回「綁定碼無效、已使用或已過期」 | 回 app 重新產生;碼 10 分鐘內有效、只能用一次 |
| 啟動時說「尚未登入」 | 先執行一次 `claude` 完成登入 |
| 啟動時說「偵測到長效 token」 | 移除環境變數 `CLAUDE_CODE_OAUTH_TOKEN`;worker 只支援本人互動登入 |
| app 顯示離線,但 worker 在跑 | 看紀錄檔有沒有「連不上 Bridge」;公司網路要允許連到 `*.ai-go.app` |
| 開機常駐沒反應 | 多半是找不到 `claude`:設 `AIGO_BRIDGE_CLAUDE` 為完整路徑 |
| 回答第一段要十幾秒 | 模型在 thinking;app 可逐次帶「關閉 thinking」(docs/08 §2) |
| 工作失敗「超過本機單一工作上限」 | 調高 `AIGO_BRIDGE_JOB_TIMEOUT_S`,或把工作拆小 |
