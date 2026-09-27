# 01 · 架構

## 1. 要解的問題

AI GO 上的 app 呼叫 LLM,常見寫法是在 Server Action 或 Hosted App 裡直接打 OpenAI / OpenRouter。
這樣做有三個問題:

1. **每支 app 各自持有金鑰、各自處理重試與錯誤**,換供應者要改好幾處。
2. **Server Action 有秒數上限**,長輸出與串流做不到。
3. **沒有辦法把工作交給使用者自己電腦上的 Claude Code**——本機沒有對外入口,雲端無法主動連進去。

本套件把這三件事收斂成一個 Hosted App(Bridge)加一支本機程式(Worker)。

## 2. 元件

```
┌─ 呼叫端 ───────────────────────────────────────────────────────────────┐
│ Custom App 前端      用 Server Action 換到 session token,直連 Bridge 串流 │
│ Custom App Action    ctx.http.call("llm-bridge", "/v1/chat/completions") │
│ 其他 Hosted App      httpx.post(BRIDGE_URL + "/v1/chat/completions")     │
└──────────────────────────────┬─────────────────────────────────────────┘
                               ▼
┌─ Bridge(Hosted App,visibility=public,自行驗章)────────────────────────┐
│ 相容端點  POST /v1/chat/completions · POST /v1/responses · GET /v1/models │
│ 前端用    POST /bridge/session(source 金鑰 → 短效 token)                 │
│ 非同步    GET  /v1/jobs/{id}                                              │
│ Worker 面 POST /worker/register · claim · jobs/{id}/chunk · result · heartbeat │
│ 路由      model 前綴 → anthropic / openrouter(原樣轉送)/ local(寫工單) │
│ 狀態      只存平台自建表:jobs / workers / usage                          │
└──────────────────────────────▲─────────────────────────────────────────┘
                               │ Worker 主動輪詢(HTTPS 出站)
┌─ Worker(使用者本人電腦)──────┴─────────────────────────────────────────┐
│ 設備鑰匙註冊 → 認領 owner=自己 的工單 → claude -p(stream-json)          │
│ → 逐段 /chunk → 完成 /result(全文、usage、cost、conversation session)  │
│ → 每 30 秒 /heartbeat                                                   │
└────────────────────────────────────────────────────────────────────────┘
```

## 3. 設計決定與它對應的平台限制

每一條決定都是被某個限制逼出來的。限制改了,決定就要回頭檢查。

| 決定 | 對應的限制 | 如果限制放寬 |
|---|---|---|
| **Bridge 是 Hosted App,不是 Custom App 的 action** | Server Action 執行上限數十秒到 120 秒;經 egress 閘道的單次對外呼叫預設 10 秒、上限 30 秒 | 仍建議保留:集中金鑰與用量帳的理由不變 |
| **Bridge 設 `public` 並自行驗章** | `internal` 的 Hosted App 由平台 proxy 代管登入,但容器內拿不到任何使用者身分;Server Action 呼叫時沒有登入 cookie,會被導去登入頁 | 平台若開放把身分注入容器,可改 `internal` |
| **串流由瀏覽器直連 Bridge** | Server Action 是一問一答,無法轉送 SSE | — |
| **瀏覽器拿短效 token,不拿 source 金鑰** | 前端程式碼對使用者完全可見 | — |
| **Server Action 分同步 / 非同步兩制** | 同步呼叫受 egress 30 秒硬上限約束 | 上限提高就放寬同步門檻 |
| **狀態只存平台自建表** | Hosted App 最多 2 個實例、無 sticky session;縮到零會清掉記憶體與磁碟 | — |
| **Worker 主動輪詢,不開對內入口** | 使用者電腦在 NAT / 公司防火牆後面;反向通道(隧道服務)會斷線,而且要每個人各自設定 | — |
| **長工作拆成多次請求** | Hosted App 單一請求上限 300 秒,SSE 連線滿 300 秒必斷 | — |
| **預設不常駐(scale-to-zero)** | 常駐會一直佔用租戶運算資源、部分方案不提供 | P1 實測冷啟動後再決定;worker 輪詢本身就是入站流量 |
| **prompt 原文預設不落表** | 自建表對同租戶的 app 普遍可讀;LLM 輸入常含個資與商業資訊 | 需要除錯時由 source 自行開 `BRIDGE_STORE_PROMPTS` |

## 4. 一次 `local/self` 呼叫的完整路徑

1. 前端呼叫自己的 Server Action → action 用 `ctx.user_id` 查出使用者 email,
   向 Bridge `POST /bridge/session` 換短效 token(帶 source 金鑰與 caller user)。
2. 前端帶 token 直連 `POST /v1/chat/completions`(`model: "local/self"`, `stream: true`)。
3. Bridge 查 workers 表:有沒有 **owner = caller user** 且最近有心跳的 worker。
   沒有 → `409 no_worker_for_user`,**不會改派給任何其他人的 worker**。
4. 有 → 寫一筆 job(`pending`),保持 SSE 連線並開始等 chunk。
5. 該 worker 下一次輪詢認領這筆 job(`leased`,租約 60 秒),啟動本機 `claude -p`。
6. worker 每收到一段文字就 `POST /worker/jobs/{id}/chunk`;Bridge 轉成 SSE 事件送給前端。
7. 結束時 `POST /result`,Bridge 寫入全文、usage、cost,SSE 送出 `[DONE]`,job 轉 `done`。
8. 任何一步逾時:租約到期回到 `pending` 一次;第二次仍失敗 → `failed: worker_lost`,
   SSE 送出錯誤事件,呼叫端拿到明確原因。

> 跨實例注意:Bridge 最多兩個實例,worker 的 `/chunk` 可能打到「沒有持有 SSE 連線」的那一個。
> 所以 chunk 一律先寫表,持有連線的實例從表讀出來送;P1 會量這個輪詢間隔對延遲的影響。

## 5. 實測依據

P1 完成後,把下列四個數字與量測方法寫在這一節,後續設計以實測為準:

1. 本機 `claude -p` 的啟動時間、首 token 延遲、總時間(Windows / macOS)
2. 瀏覽器從 Custom App 執行頁直連 Bridge 的 SSE 是否可行(CORS、token、斷線行為)
3. Server Action 經 egress 同步呼叫 Bridge 的實際可用秒數
4. worker 以固定間隔輪詢縮到零的 Bridge 時,冷啟動命中率與延遲
