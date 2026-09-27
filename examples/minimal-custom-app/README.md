# minimal-custom-app:接上 Bridge 的最小 Custom App

兩頁:「連接我的電腦」(綁定自己的 Claude Code)與「對話」(瀏覽器直連串流 + 伺服器端同步呼叫)。
以 `starter-internal` 起手式建立,**這裡只放要覆蓋或新增的檔案**;其餘(版面元件、`App.css`、
`main.tsx`、平台 SDK)沿用起手式原樣。起手式附的示範 action、示範頁與 `_template.json` 要刪掉
(`_template.json` 宣告了用不到的外部服務,不刪發布會被擋)。

| 檔案 | 作用 |
|---|---|
| `actions/bridge_session.py` | 用 source 金鑰換短效 session token(綁 `ctx.user_id`),前端拿去直連 Bridge |
| `actions/bridge_computers.py` | 產生綁定碼、列出與撤銷「我的電腦」 |
| `actions/bridge_chat.py` | 伺服器端同步呼叫,帶 `X-Bridge-Wait: 20`,超過回工單 id |
| `src/lib/bridge.ts` | 前端客戶端:session 快取、SSE 解析、`[DONE]` 判斷完整性 |
| `src/pages/ConnectPage.tsx` | 綁定碼與電腦清單 |
| `src/pages/ChatPage.tsx` | 模型、effort、thinking 逐次指定;串流與伺服器端兩種呼叫 |

## 前置設定(Builder 或 API)

1. 外部服務:slug **`llm-bridge`**,base_url 指向 Bridge(例 `https://<your-bridge>.deploy.ai-go.app`),
   `timeout_ms` 設 30000,並授權給本 app。slug 在程式裡必須是字面字串,發布閘門才認得。
2. secrets:`BRIDGE_KEY`(Bridge 發給這個 app 的 source 金鑰,即 Bridge 端 `BRIDGE_KEY__<SOURCE>` 的值)、
   `BRIDGE_PUBLIC_URL`(Bridge 對外網址,前端直連串流用)。
3. Bridge 必須部署在 `*.ai-go.app` 網域下:Custom App 執行頁的 CSP `connect-src` 只放行這個範圍。

## 兩條呼叫路徑怎麼選

| 情境 | 走法 | 上限 |
|---|---|---|
| 要逐字顯示給使用者看 | 前端 `streamChat()` 直連 | Hosted 單一請求 300 秒;Bridge 在 280 秒主動收尾並送 `stream_timeout` |
| action 裡要拿結果接著處理 | `bridge_chat` | egress 閘道 30 秒硬牆;20 秒沒做完回 202,用 `op="job"` 查 |

串流是否完整只看一件事:收到 `[DONE]` 且之前沒有 `error` 事件。連線被平台切斷時不會有錯誤狀態碼。
