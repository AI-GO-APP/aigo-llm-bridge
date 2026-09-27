# 術語表

這些詞在本 repo 有精確的意思,文件、程式碼、錯誤訊息都照這裡用。

| 詞 | 意思 | 不是 |
|---|---|---|
| **Bridge** | 部署成 AI GO Hosted App 的閘道服務。對外講 OpenAI 相容的線路,對內把請求路由到某個 provider | 不是 worker,也不跑模型 |
| **Provider** | Bridge 背後實際產生回應的來源:`anthropic`、`openrouter`、`local` 三種 | — |
| **`local` provider** | 由使用者本人電腦上的 Claude Code 產生回應。Bridge 只負責把工單交給對的 worker | 不是「一台共用的 Claude 機器」 |
| **Worker** | 裝在使用者本人電腦上的程式。主動向 Bridge 領工單、呼叫本機 `claude -p`、回傳結果 | 不接受任何對內連線 |
| **Owner** | worker 的擁有者,以 AI GO 平台使用者 id(Server Action 的 `ctx.user_id`)識別。一台 worker 只屬於一個 owner,綁定只能在 app 內由本人完成 | 不是使用者自填的 email |
| **Job(工單)** | 一次 `local` 呼叫。存在平台自建表,狀態 `pending → leased → streaming → done / failed` | 不存在記憶體裡 |
| **Lease(租約)** | worker 認領工單後的有效期限。逾期沒回報,工單回到 `pending` 一次,再逾期就 `failed` | — |
| **Source** | 呼叫 Bridge 的那支 app。每個 source 有自己的金鑰(`BRIDGE_KEY__<SOURCE>`),用量帳按 source 分 | — |
| **Caller user** | 這次呼叫是替哪位使用者做的(平台使用者 id)。`local/self` 靠它配到 owner 相同的 worker | 不是 source |
| **Session token** | Bridge 發給瀏覽器的短效憑證(預設 1 小時),讓前端直連 Bridge 串流,而不必把 source 金鑰放進瀏覽器 | 不是平台登入憑證 |
| **Conversation session** | Claude Code 的對話 id(UUID)。帶 `X-Bridge-Session` 可以讓同一段對話跨多次呼叫延續 | 不是 session token |
| **同步呼叫** | 呼叫端等 Bridge 直接回結果。受呼叫端自己的秒數上限約束 | — |
| **非同步呼叫** | 帶 `X-Bridge-Async: true`,Bridge 立刻回 `202 {job_id}`,結果之後查 | — |

## 平台用語(沿用 AI GO)

| 詞 | 意思 |
|---|---|
| Custom App | AI GO 平台內的 React 前端 + Python Server Action 應用 |
| Hosted App | AI GO 代管的容器應用(自帶框架),本套件的 Bridge 部署成這一種 |
| Server Action | Custom App 的後端函式 `execute(ctx)`,有執行秒數上限 |
| Egress slug | Server Action 對外呼叫時用的外部服務代號(`ctx.http.call(<slug>, <path>)`) |
| 自建表 | 租戶資料中心裡由開發者建立的資料表 |
