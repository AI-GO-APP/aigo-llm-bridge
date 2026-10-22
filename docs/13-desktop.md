> **歷史產品線文件**：本頁描述舊 Hosted／個人端點流程；現行 BYO Windows 請讀 [產品入口](README.md)、[架構](ARCHITECTURE.md) 與 [API](API.md)。不要以本頁定義新版契約。

# 13 · 個人本機端點（macOS／Windows）

供本人本機程式呼叫自己的 Claude Code／Codex 訂閱。沿用 CLI 的官方登入流程，不讀取或轉送 OAuth 憑證。
此模式與原有 Hosted Bridge／worker 獨立；不改既有 `/worker/*` 協定與 `local/self` 語意。
若要讓 AI GO 上的 app 呼叫，仍使用 [部署 Bridge](03-deploy-bridge.md) 與 [worker 綁定](04-worker.md)；
個人端點只有 loopback，不是可供遠端 app 直連的公開 URL，目前 Hosted worker 仍只支援 Claude Code。

## 安裝與登記

- [macOS](../desktop_platform/macos/README.md)：`python3 desktop_platform/macos/install.py`
- [Windows](../desktop_platform/windows/README.md)：`py -3 desktop_platform\windows\install.py`

先用 `claude` 登入本人 Claude 訂閱、`codex login` 選擇 ChatGPT 登入。
登入狀態由 `claude auth status --json`／`codex login status` 檢查，沒有登入的 provider 回 `503 login_required`。
不要求兩個都登入，已登入的可各自使用。登入後重跑安裝程式或 `aigo_desktop.py setup` 更新登記。
Codex 必須支援 `exec --ignore-user-config --ignore-rules --ephemeral`；不支援的舊版回報 provider 失敗，需先更新 CLI。
登入過期、方案無權使用指定模型或額度耗盡時，需在原 CLI 處理，不自動轉 API 計費。

設定在 `~/.aigo-llm-bridge/desktop/desktop.json`；CLI 路徑可用 `AIGO_DESKTOP_CLAUDE`／`AIGO_DESKTOP_CODEX` 指定。
安裝時產生獨立隨機 Bridge 金鑰，不是 OpenAI／Anthropic 的 API key。更新與移除服務保留金鑰；
完全移除時先移除背景服務，再刪除 desktop 設定目錄（不影響原 worker 綁定）。
`AIGO_DESKTOP_HOME` 可指定另一個目錄，使用所有指令時須維持一致。

## 端點與金鑰

- Base URL：`http://127.0.0.1:8790/v1`
- Bearer API key：執行已安裝的 `aigo_desktop.py credentials` 查看。`status` 不顯示金鑰。
- `GET /healthz`：實際登入狀態；`GET /v1/models`：已登記 CLI。
- `POST /v1/chat/completions`：`model` 用 `claude`、`codex`，或 `claude/sonnet`、`codex/<可用模型>`。
- 瀏覽器開啟 `/`、`/v1` 或 `/v1/` 可看到連線說明頁、複製 Base URL，貼上金鑰測試連線。
  說明頁不包含金鑰或帳號，輸入的金鑰不寫入瀏覽器儲存空間；測試只查模型清單、不呼叫模型。
- 除上述公開說明頁，所有 API 端點都要 Bearer 金鑰；同時只執行一個推論，忙碌回 429，單次上限 180 秒。

Python OpenAI SDK 範例（API key 從自己的環境變數取得）：

```python
import os
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8790/v1", api_key=os.environ["AIGO_LOCAL_API_KEY"])
reply = client.chat.completions.create(
    model="codex", messages=[{"role": "user", "content": "請用一句話介紹你自己"}])
print(reply.choices[0].message.content)
```

目前只支援非串流文字對話；不接受工具、圖片與 response_format，不提供 token usage。
Claude 禁用工具及 MCP；Codex 使用 read-only sandbox、關閉 shell／多代理／搜尋且略過使用者設定。
個人端點不開 CORS、不監聽 LAN，金鑰供本人程式使用。不要把訂閱憑證或 Bridge 金鑰分享給其他人。
CLI 仍依各服務可用方案、模型與額度限制運作。
官方參考：[Codex 非互動模式](https://learn.chatgpt.com/docs/non-interactive-mode)、
[Codex 登入](https://learn.chatgpt.com/docs/auth)。

## Repo 分工與獨立發布

沿用本地既有桌面專案的模式：共用核心、平台介面、平台封裝三層。

| 目錄 | 責任 | 允許依賴 |
|---|---|---|
| `desktop/` | 個人 API、登入登記、金鑰、CLI 呼叫與共同安裝檔案 | Python 標準函式庫 |
| `desktop_platform/macos/` | LaunchAgent、Mac 安裝／移除與測試 | 共用核心 |
| `desktop_platform/windows/` | 使用者排程、Windows ACL、安裝／移除與測試 | 共用核心 |
| `packaging/macos/`／`packaging/windows/` | 各平台封裝入口 | 共用封裝工具 |
| `hosted/`／`worker/`／`clients/` | 原有 Hosted Gateway 功能 | 不依賴新平台層 |

平台不得互相匯入；單一平台變更只觸發自己的桌面 CI，共用核心或 VERSION 變更觸發兩邊。
原有 Hosted CI 保留。兩個平台的安裝目錄、服務名稱相互獨立；一個平台失敗不阻止另一個平台單獨發布。

`.github/workflows/desktop-macos.yml`／`desktop-windows.yml`：各自原生 runner 測試、封裝、上傳 artifact。
`.github/workflows/desktop-publish.yml`：在 main 手動選擇平台，必須先通過該平台測試並驗證 manifest 的
commit、版本、大小、SHA256 才發布，標籤分別為 `desktop-macos-vX.Y.Z`／`desktop-windows-vX.Y.Z`。
不覆蓋已發布版本。版本沿用根目錄 VERSION，兩平台可分批採用同一核心版本，無須一起發布。

包是需要 Python 的原始碼安裝 ZIP，非獨立 EXE／APP、未簽章，亦未經 Apple 公證；manifest 明確記載。
封裝採檔案白名單，不包含登入憑證、設定、測試資料或另一平台的檔案。
未建立遠端 PR、未跑 GitHub Actions 或未發布時，不能把本地包稱為已發布版本。
