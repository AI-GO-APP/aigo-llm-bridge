# 10 · 疑難排解

依「你看到什麼」查。每一列都是實際遇過的狀況。

## 呼叫端

| 看到 | 原因 | 處理 |
|---|---|---|
| `409 priority_required` | 使用者還沒選優先順序 | 顯示選擇卡,`PUT /bridge/preferences`(docs/05 §3.2) |
| `409 no_worker_for_user` | 用了 `local/*`,而使用者的電腦沒連線 | 請使用者執行 worker;或改用 `auto` 讓它自動改用雲端 |
| 回應 `fallback` 一直不是 null | 優先的那一側一直失敗 | 看 `fallback.reason`:本機多半是電腦沒開,雲端看是限流還是金鑰 |
| `400 bad_auto_models` | `models` 放了兩個本機或兩個雲端,或放了不認得的前綴 | 各放一個 `local/*` 與一個 `openrouter/*` / `anthropic/*` |
| `400 user_required` | `auto` 或 `local/*` 沒帶使用者 | 帶 `X-Bridge-User`,或用 session token |
| `502 provider_auth` | Bridge 的**雲端金鑰**無效 | 管理者換 `OPENROUTER_API_KEY`;不是呼叫端的憑證錯 |
| `503 provider_not_configured` | Bridge 沒設那個雲端的金鑰 | 設金鑰,或不要指定那個後端 |
| 串流在 280 秒結束、`stream_timeout` | 單一連線上限 | 用事件裡的 `job_id` 查 `/v1/jobs/{id}` 取全文 |
| 串流中途斷掉、沒有 `[DONE]`、沒有錯誤 | 連線被平台或網路切斷 | 視為不完整;重送 |
| 回答第一段要十幾秒 | 模型在 thinking | 對話型呼叫帶 `reasoning: {enabled: false}`(docs/08 §2) |
| `dropped` 有 `thinking_off` | 那個模型關不掉 thinking(Opus 5.5、Fable) | 換模型,或接受 |

## Custom App

| 看到 | 原因 | 處理 |
|---|---|---|
| action 約 30 秒後失敗,或 status `timeout` | egress 閘道 30 秒硬牆 | 用 `bridge_block.py`(帶 `X-Bridge-Wait: 20`),處理 `pending` |
| `served_by` / `fallback` 永遠是空的 | 從標頭讀,但 `ctx.http.call` 拿不到回應標頭 | 讀本體的 `x_bridge`(區塊已這樣做) |
| 發布被擋:動態 slug、egress 未授權 | slug 用變數傳入,或外部服務沒授權 | slug 寫成字面字串;Builder 授權 `llm-bridge` |
| 發布被擋:`_template.json` 宣告的服務 | 起手式殘留 | 刪掉 `_template.json` 與示範 action |
| action 回 503「App runner 暫時不可用」 | 剛發布的冷啟動,或租戶配額滿(回應帶 `quota_hint`) | 等 `Retry-After` 再試;配額問題不是程式錯 |
| 瀏覽器直連被 CSP 擋 | Bridge 綁了自訂網域 | 用 `*.deploy.ai-go.app` 網址 |
| 畫面上找不到元素(自動化測試) | 頁面在 Shadow DOM 裡 | 用 `data-testid`,從 shadowRoot 查 |

## 部署與平台

| 看到 | 原因 | 處理 |
|---|---|---|
| 部署失敗 `exceeded quota: aigo-quota` | 共用池租戶配額不夠新舊兩個執行個體同時存在 | 等其他 app 縮下來再部署(docs/03 §7) |
| 設 `resources` 回 403 `RESOURCES_REQUIRE_DEDICATED_NODES` | 共用池租戶不能自設執行上限 | 不要設;`hosted_env.py` 預設就不送 |
| 平台 API 回 401「帳號或密碼錯誤」,但密碼沒錯 | 打到 apex `https://ai-go.app` | `AIGO_BASE_URL` 用租戶空間 `https://<tenant>.ai-go.app` |
| `/healthz` 的 `sources` 是 0 | 環境變數沒生效 | `python tools/hosted_env.py --slug <slug> --show` 看 key 有沒有在 |
| 綁定時 500(舊版) | 平台表把數字欄讀回成字串 | 升級到 0.1.0 以上 |
| Hosted App 設 `internal` 後全部 401 或被導去登入頁 | `internal` 拿不到呼叫者身分 | Bridge 必須是 `public`,靠自己的金鑰驗證 |
| 建 Hosted App 回 422「已被使用」 | 這個 slug 曾經被用過;刪除過的 App 會永久保留 slug | 換一個 slug;測試用的名字不要取正式要用的 |
| 剛綁好的電腦顯示離線 | 綁定不等於在線,要等 `run` 送出第一次心跳 | 在電腦上執行 `run` |

## worker

| 看到 | 原因 | 處理 |
|---|---|---|
| 「尚未登入」 | Claude Code 沒登入 | 執行一次 `claude` 完成登入 |
| 「偵測到長效 token」 | 有 `CLAUDE_CODE_OAUTH_TOKEN` | 移除;worker 只支援本人互動登入 |
| 「設備鑰匙已失效或被撤銷」後結束 | 在 app 被撤銷 | 需要的話重新綁定 |
| 「claude 結束碼 2」 | 找不到 claude 或參數被殼層吃掉 | Windows 直接指到 `claude.exe`;設 `AIGO_BRIDGE_CLAUDE` |
| 「超過本機單一工作上限」 | 工作超過 `AIGO_BRIDGE_JOB_TIMEOUT_S` | 調高,或把工作拆小 |
| 回答裡有 `[redacted]` | 遮罩把 email 或本機路徑換掉了 | 正常行為(docs/04 §7) |
| 長串英數(JSON、雜湊)延遲出現(舊版) | 遮罩扣住整段英數字 | 升級到 0.1.0 以上(最多扣 64 字元) |
