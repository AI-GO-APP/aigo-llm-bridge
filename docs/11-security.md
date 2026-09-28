# 11 · 機敏資訊與安全

這份整理「有哪些金鑰、各放在哪裡、絕不能出現在哪裡、外洩了怎麼辦」。
部署者、app 開發者、維護這個 repo 的人都要讀;其他文件講到金鑰時只連回這裡。

## 1. 一句話原則

**金鑰只存在兩種地方:平台的 secrets／環境變數,以及你自己的密碼管理工具。**
不進 repo、不進瀏覽器、不進指令列、不貼進 AI 對話、不寫進文件或 issue。

## 2. 機敏資訊清單

| 名稱 | 是什麼 | 應該放在 | 絕不能出現在 | 怎麼換 |
|---|---|---|---|---|
| `BRIDGE_KEY__<SOURCE>` | Bridge 發給某個呼叫端 app 的 source 金鑰 | Bridge 的環境變數;呼叫端 Custom App 的 secrets(`BRIDGE_KEY`)、Hosted App 的環境變數 | 前端程式碼、瀏覽器、`examples/` 以外的任何檔案 | docs/07 §3 |
| `BRIDGE_SESSION_SECRET` | 簽瀏覽器 session token 的密鑰 | 只有 Bridge 的環境變數 | 任何呼叫端 | docs/07 §3 |
| `OPENROUTER_API_KEY`、`ANTHROPIC_API_KEY` | 組織的雲端 LLM 金鑰,按量計費 | 只有 Bridge 的環境變數 | 任何呼叫端;呼叫端永遠只拿 source 金鑰 | 到發行方撤銷、重發,再更新 Bridge |
| Session token | Bridge 發給瀏覽器的短效憑證(最長 1 小時,綁定一位使用者) | 瀏覽器**記憶體**(`bridge.ts` 只存在模組變數,不寫 localStorage) | 網址、紀錄檔、localStorage | 自動過期;換 `BRIDGE_SESSION_SECRET` 會讓全部失效 |
| worker 設備鑰匙 | 一台電腦與一位 owner 的綁定 | `~/.aigo-llm-bridge/worker.json`(macOS／Linux 設為只有本人可讀;Windows 依使用者目錄權限) | 別人的電腦、共用資料夾、雲端硬碟同步目錄 | 在 app 撤銷後重新綁定 |
| 平台憑證(`AIGO_TOKEN`、帳密) | 部署工具呼叫 AI GO 平台 API 用 | 環境變數,或 aigo-builder 的 `~/.aigo/.env` | 本 repo 的任何檔案、指令列參數 | 平台上登出／改密碼 |
| `INTERNAL_KEY`(範例) | `examples/hosted-app-caller` 驗證上游呼叫者 | 那個 Hosted App 的環境變數 | 瀏覽器 | 改環境變數並同步上游 |
| 禁字清單 | 不能出現在 repo 的客戶、租戶、專案與人名 | GitHub repository **secret** `BANNED_TERMS`;本機 `.banned-terms`(已 gitignore) | repository variable、任何會印進 CI 紀錄的地方 | 改 secret |

## 3. 部署時的 `bridge.env`

docs/03 §2 讓你把產生的金鑰寫進 `bridge.env`,再用 `tools/hosted_env.py` 設到 Bridge。

- `.gitignore` 已排除 `*.env`,但**最好不要放在 repo 目錄裡**:放在 repo 外的工作目錄更不會誤提交。
- 設定完成後把值存進組織的密碼管理工具,**本機的 `bridge.env` 就可以刪掉**。之後換金鑰只要寫一個
  只含那幾個 key 的新檔案再跑 `hosted_env.py`——它會先讀現況再合併,只改你給的 key。
- `hosted_env.py` 與其他工具的輸出**不會印出任何值**;`--show` 只列出有哪些 key。
- 不要用 `KEY=value python ...` 或 `--token xxx` 這種寫法把值放進指令列,shell 歷史會留下來。

## 4. 什麼資料會被保存

| 資料 | 預設行為 |
|---|---|
| 提示與回應原文 | **不長期保存**。本機工單的提示在完成或失敗時立即清除;`BRIDGE_STORE_PROMPTS=1` 才保存(只在除錯時開,用完關掉) |
| `biz_bridge_usage` | 只有 token 數、成本、耗時、結果、使用者 id,不存內容 |
| worker 的紀錄檔 | 每個工作一行開始與結束,不印提示內容 |
| 回應內容 | worker 送回前把帳號 email、同網域 email、本機路徑換成 `[redacted]`(docs/04 §7) |

內容會送到哪裡:本機那一側送到**使用者本人登入的** Anthropic 帳號;雲端那一側送到組織的 OpenRouter／Anthropic。
資料分類與客戶合約是否允許,由導入的組織判斷(docs/02 §4)。

## 5. 呼叫端的四條硬規則

1. source 金鑰只在伺服器端(Server Action 的 secrets、Hosted App 的環境變數);瀏覽器改用 `bridge_session` 換來的 session token。
2. 使用者身分來自平台(`ctx.user_id`)或你自己的登入機制,**不能讓瀏覽器自己宣稱**——身分決定工作交給誰的電腦。
3. 綁定碼只能由伺服器端代表登入者產生(Bridge 本來就不接受 session token 產生綁定碼)。
4. 錯誤訊息與紀錄不要回顯請求標頭;`Authorization` 裡就是金鑰。

## 6. 這個 repo 是公開的

- 任何東西只要進過一個 commit,就當成已公開——刪檔、改寫歷史都不能保證收回(fork、快取、CI 紀錄)。
- CI 每次都跑兩道檢查:
  - `lint-terms`:不能出現特定客戶、租戶、專案或人名(含 commit 訊息與作者名)
  - `secrets`:`tools/scan_secrets.py --history`,擋常見金鑰格式、機敏變數被賦予真值、`*.env` 之類的檔案
- 兩支工具的輸出都**不印出命中的內容**,只印位置——CI 紀錄是公開的。
- CI 裡要用機敏值,一律用 GitHub **secret**,**不要用 repository variable**:variable 放在 `env:` 裡會在
  每個步驟開頭以明文印出。
- 範例一律用 `<your-tenant>`、`<your-bridge>` 這類佔位;測試裡的假金鑰若被誤判,在那一行加 `scan-secrets: allow`。

本機提交前可以先跑:

```bash
python tools/scan_secrets.py
python tools/lint_terms.py --commits     # 本機要有 .banned-terms 才檢查得到
```

## 7. 外洩了怎麼辦

1. **先換,再查**。換的方法見 docs/07 §3;雲端金鑰要到 OpenRouter／Anthropic 撤銷。
2. 查 `biz_bridge_usage` 那段時間該 `source` 的呼叫量與成本,確認有沒有被濫用。
3. 金鑰進過 repo 的話:換掉之後再移除檔案,並在 PR 裡寫明已換過。**不要只刪檔不換。**
4. worker 的設備鑰匙外洩(例如 `worker.json` 被複製):在 app 撤銷那台電腦,重新綁定。
