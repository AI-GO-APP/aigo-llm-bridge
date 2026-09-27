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

1. 前端呼叫自己的 Server Action → action 以平台身分 `ctx.user_id` 當 caller user,
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

後續設計以這一節的實測為準。腳本在 [`spikes/`](../spikes/),可以重跑;數字變了就回頭檢查第 3 節的決定。

### S1 · 本機 `claude -p` 延遲(Windows,Claude Code 2.1.258,訂閱登入)

量法:`spikes/cli-latency/probe.py`,同一題重複執行,起點都是「行程啟動」,單位毫秒。
旗標:`-p --tools "" --max-turns 1 --strict-mcp-config --setting-sources "" --system-prompt …
--output-format stream-json --include-partial-messages --verbose`,**extended thinking 關閉**。

| 模型 | 行程就緒 | 第一段文字 | 文字完成(`message_stop`) | `result` 事件 | 行程結束 | 每次成本(估) |
|---|---|---|---|---|---|---|
| haiku(n=5) | 930 | **1,620** | ≈2,400 | 3,509 | 4,046 | $0.0009 |
| sonnet(n=3) | 916 | **2,064** | — | 3,729 | 4,265 | $0.0019 |

同一題**開著 thinking**:首段文字 10,287 ms、1,399 個 thinking token、$0.0077,而且模型會忽略
`--system-prompt` 裡的指令(關掉之後照做)。

驗證項:

| 項目 | 結果 |
|---|---|
| `--session-id` 開場、`--resume` 續問,記得上一輪 | ✅ |
| `--system-prompt` 取代預設提示後照規則回答(thinking 關閉時) | ✅ |
| 工具清單為空(`init.tools = []`) | ✅ |
| 直接問「你看到哪些附加資訊」,回答不含 email / 本機路徑 / 作業系統 | ✅(有加「不得提及」條款時) |

### S2 · 瀏覽器從 Custom App 執行頁直連 Bridge

| 項目 | 結果 |
|---|---|
| 平台邊緣會不會緩衝 SSE | **不會**:伺服端每 400 ms 送一段,客戶端收到的間隔也是 400 ms |
| Custom App 執行頁的 CSP | `connect-src 'self' https://ai-go.app https://*.ai-go.app …` —— Hosted App 的 `*.deploy.ai-go.app` **在允許範圍內** |
| 從執行頁來源發出的 CORS 預檢 | 通過(`Access-Control-Allow-Origin: *`,允許 `Authorization`) |
| Hosted App 改環境變數後生效 | 數秒內換上新實例(以 `/healthz` 的版本標記確認) |
| 瀏覽器實際串流、錯誤可讀性、長連線截斷點 | 待補(需要在執行頁登入後操作) |

### S3 · Server Action 經 egress 同步呼叫 Bridge

量法:`spikes/custom-app-client` 的 `spike_sync`,Bridge 刻意延遲 N 秒才回;外部服務 `timeout_ms` = 30000,
action 的 `timeout_ms` = 120000。

| 伺服端延遲 | 結果 |
|---|---|
| 1 – 29 秒 | 成功;平台額外開銷約 70 – 150 ms |
| 31 秒 | `ctx.http.call` **回傳**錯誤 `egress_upstream_error`(約 30.0 秒),action 本身繼續執行 |
| 45 秒 | **整支 action 被砍**:`status: timeout`,`Action 執行超時(30000ms)` |

另外:閒置後第一次呼叫 action,牆鐘 7.7 秒、實際執行 1.2 秒 —— action runner 冷啟動約 **6.5 秒**。

### 端到端(本機 Bridge + 真 worker + 官方 openai 客戶端)

量法:`tools/e2e_local.py`,Bridge 以記憶體存放跑在本機,worker 以擁有者本人登入的 Claude Code 執行,
呼叫端是官方 `openai` Python 客戶端(只改 `base_url`)。模型 `local/self:haiku`。

| 項目 | 結果 |
|---|---|
| 同步回應 | ✅ 3.45 秒 |
| 串流 | ✅ 第一段內容 1.6 秒、全文 4.9 秒 |
| JSON schema(`response_format`) | ✅ 回傳符合 schema 的物件 |
| 對話延續(`X-Bridge-Session`) | ✅ |
| 問它看到哪些附加資訊 | ✅ 回答不含 email |
| 別的使用者呼叫 `local/self` | ✅ 409 `no_worker_for_user` |

### S4 · worker 輪詢縮到零的 Bridge

量測中(`spikes/cold-poll/probe.py`)。

### 由實測得出的決定

| 決定 | 依據 |
|---|---|
| worker 預設**關閉 extended thinking**(以 `--settings '{"alwaysThinkingEnabled": false}'`),呼叫端可逐次開啟 | S1:延遲 6 倍、成本 9 倍,且系統提示不被遵守 |
| worker 在 `message_stop` 就交付全文,`result` 到了再補 usage / cost | S1:兩者之間有約 1.3 秒的收尾摘要,另加 0.5 秒行程結束 |
| worker 永遠在**專用的空目錄**執行、加「不得提及附加資訊」條款、並對輸出做**確定性遮罩**(帳號 email、本機路徑) | Claude Code 會在每一輪附上環境快照與登入帳號 email,且沒有設定可以關掉;條款在測試中有效,遮罩是第二道防線 |
| Windows 上直接呼叫 `claude.exe`,不經 `claude.cmd` | `.cmd` 殼會重新解析引號,`--tools ""` 這類空字串參數有被吃掉的風險 |
| 不用 `--bare` | `--bare` 不讀訂閱登入 |
| **Bridge 必須留在 `*.ai-go.app` 網址,不能綁自訂網域** | S2:執行頁 CSP 只允許 `*.ai-go.app`;綁自訂網域後瀏覽器直連會被擋 |
| 瀏覽器不能直接打任何模型供應者 | 同上,CSP 不允許 |
| Server Action 同步模式的預設上限定在 **20 秒**,超過自動轉非同步 | S3:硬牆在 30 秒,而且撞牆時有兩種不同的失敗形狀,留 10 秒餘裕 |
| 呼叫端必須同時處理「`ctx.http.call` 回傳錯誤」與「action 被砍」兩種逾時 | S3 |
| 呼叫端區塊在 `ctx.http.call` 裡**寫死字面 slug** | 發布閘門只認得字面 slug;用常數傳入會被標成「動態 slug」而無法檢查授權 |
| worker 的擁有者以平台身分 `ctx.user_id` 為準,由 app 內的「連接我的電腦」流程綁定 | Server Action 拿得到的是 `ctx.user_id`,不是 email;身分來自平台而不是使用者自填 |
