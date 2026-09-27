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
| **Bridge 一律用冷啟動模式(`always_on=false`),非必要不開常駐** | 常駐會一直佔用租戶運算資源、部分方案不提供;S4 實測冷啟動模式下閒置 15 分鐘仍保留實例,而且有 worker 在線時長輪詢本身就讓它保持溫熱 | 只有在「沒有 worker、又要求第一個請求不能等冷啟動」時才考慮開,並寫下理由與退場條件 |
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
--output-format stream-json --include-partial-messages --verbose`,這一組量測時關閉了 thinking。

| 模型 | 行程就緒 | 第一段文字 | 文字完成(`message_stop`) | `result` 事件 | 行程結束 | 每次成本(估) |
|---|---|---|---|---|---|---|
| haiku(n=5) | 930 | **1,620** | ≈2,400 | 3,509 | 4,046 | $0.0009 |
| sonnet(n=3) | 916 | **2,064** | — | 3,729 | 4,265 | $0.0019 |

驗證項:

| 項目 | 結果 |
|---|---|
| `--session-id` 開場、`--resume` 續問,記得上一輪 | ✅ |
| 工具清單為空(`init.tools = []`) | ✅ |
| 直接問「你看到哪些附加資訊」,回答不含 email / 本機路徑 / 作業系統 | ✅(有加「不得提及」條款時) |

> **撤回的結論**:早期版本寫「開著 thinking 會忽略系統提示,worker 應預設關閉」。那只來自一題刻意刁難的測試
> (不管問什麼都只能回四個字),樣本與題型都不足以推論;S1b 的矩陣結果相反,見下。

### S1b · 每次呼叫指定模型、effort、thinking 的影響

量法:`spikes/cli-thinking/probe.py`。3 個模型別名 × 4 種設定 × 2 題(「只輸出指定 JSON」與一般問答)× 2 次,
共 48 次,中位數。系統提示與 worker 相同。

| 別名 → 實際型號 | 設定 | 第一段文字 | thinking token | 每次成本 | JSON 格式遵守 |
|---|---|---|---|---|---|
| `haiku` → claude-haiku-4-5 | 不帶參數 | 3.0 秒 | 177 | $0.0018 | 2/2 |
| | `--effort low` / `high` | 3.3 / 3.4 秒 | 190 / 197 | $0.0018 | 1/2 / 2/2 |
| | `MAX_THINKING_TOKENS=0` | **1.5 秒** | 0 | **$0.0008** | **0/2**(多包了程式碼區塊標記) |
| `sonnet` → claude-sonnet-5 | 四種設定 | 2.2 – 2.6 秒 | 0 | $0.002 | 全部 2/2 |
| `opus` → **claude-opus-5** | 四種設定 | 2.0 – 2.5 秒 | 0 | $0.0085 | 全部 2/2 |

讀法:

- **thinking 不該預設關閉。** haiku 關掉後快一倍、便宜一半,但格式遵守變差;要不要換這個取捨,應由呼叫端逐次決定。
- sonnet、opus 在簡單題上本來就幾乎不 thinking,四種設定差異很小;複雜題才會拉開,屆時同樣交給呼叫端指定。
- `--effort` 對 Haiku 4.5 沒有作用(該模型不支援 effort,也不報錯)。
- **別名解析因帳號而異**:官方文件說 `opus` 指向 Opus 5.5,這個帳號實測是 claude-opus-5。
  要結果可預期就傳完整模型 ID,並以回應裡的實際型號為準。
- 官方文件:`MAX_THINKING_TOKENS=0` 對 Opus 5.5 與 Fable 系列無效,這兩個只能用 effort 調整。

### S2 · 瀏覽器從 Custom App 執行頁直連 Bridge

| 項目 | 結果 |
|---|---|
| 平台邊緣會不會緩衝 SSE | **不會**:伺服端每 400 ms 送一段,客戶端收到的間隔也是 400 ms |
| Custom App 執行頁的 CSP | `connect-src 'self' https://ai-go.app https://*.ai-go.app …` —— Hosted App 的 `*.deploy.ai-go.app` **在允許範圍內** |
| 從執行頁來源發出的 CORS 預檢 | 通過(`Access-Control-Allow-Origin: *`,允許 `Authorization`) |
| Hosted App 改環境變數後生效 | 數秒內換上新實例(以 `/healthz` 的版本標記確認) |
| 瀏覽器實際串流、錯誤可讀性、長連線截斷點 | ✅ 見下方「部署在平台上的端到端」 |

### S3 · Custom App 的 Server Action 經 egress 同步呼叫 Bridge

> **適用範圍**:只有「Custom App 的 Server Action → `ctx.http.call` → Bridge」這一條路。
> 30 秒是 egress 閘道(外部服務的 `timeout_ms` 上限)的限制,**不是 Hosted App 的限制**;
> 瀏覽器直連 Bridge、其他 Hosted App 直接呼叫 Bridge 都不經過它。Hosted App 自己的上限見 S5。

量法:`spikes/custom-app-client` 的 `spike_sync`,Bridge 刻意延遲 N 秒才回;外部服務 `timeout_ms` = 30000,
action 的 `timeout_ms` = 120000。

| 伺服端延遲 | 結果 |
|---|---|
| 1 – 29 秒 | 成功;平台額外開銷約 70 – 150 ms |
| 31 秒 | `ctx.http.call` **回傳**錯誤 `egress_upstream_error`(約 30.0 秒),action 本身繼續執行 |
| 45 秒 | **整支 action 被砍**:`status: timeout`,`Action 執行超時(30000ms)` |

另外:閒置後第一次呼叫 action,牆鐘 7.7 秒、實際執行 1.2 秒 —— action runner 冷啟動約 **6.5 秒**。

### S5 · Hosted App 本身的時間上限(不經 egress)

量法:`spikes/hosted-timeout/probe.py`,從外部直接打 Hosted App,三種形狀同時送出。Hosted App 為冷啟動模式。

| 形狀 | 目標 | 結果 |
|---|---|---|
| 非串流(整段不送任何位元組) | 60 / 120 / 240 / 290 秒 | ✅ 成功 |
| | 305 / 330 / 600 秒 | ❌ 都在 **300.2 秒**回 504,內容 `activator request timeout` |
| 串流,每 5 秒一個心跳 | 330 / 620 秒 | ❌ **持續有資料也照樣在 300.2 秒被切**;狀態碼早已是 200,連線直接關閉,收不到 `[DONE]` |
| 串流,送一段後沉默 | 120 / 250 秒 | ✅ 成功 —— **沒有比 300 秒更短的閒置逾時** |
| | 330 秒 | ❌ 300.2 秒被切 |

讀法:

- **Hosted App 的上限是「單一請求 300 秒」**,不分串流與否、有沒有持續送資料。
- 串流被切時不會有錯誤狀態碼,只是連線中斷;呼叫端必須把「沒收到 `[DONE]`」當成內容不完整。
- worker 可以沉默很久才吐第一段字(至少 250 秒),平台不會因為閒置而切斷。

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

### 部署在平台上的端到端(Custom App 執行頁 + Hosted Bridge + 本機 worker)

量法:`examples/minimal-custom-app` 發布成 internal Custom App,Bridge 部署成 public Hosted App
(冷啟動模式、資料放平台自建表、**不設任何雲端模型金鑰**),worker 以擁有者本人登入的 Claude Code 執行。
在執行頁登入後操作;畫面在 Shadow DOM 裡,以 `data-testid` 驅動。

| 項目 | 結果 |
|---|---|
| 還沒綁電腦就送出 | ✅ 409,畫面顯示「請先連接我的電腦」 |
| 產生綁定碼 → 本機 `enroll` → 清單顯示「在線」 | ✅ |
| 瀏覽器直連串流(haiku,thinking 照模型預設) | ✅ 第一段文字約 12 – 23 秒:前段全是 thinking,文字要等它結束 |
| 同一題、`reasoning.enabled=false` | ✅ 第一段文字 2.4 秒、全部 7.9 秒 |
| fable + 關 thinking + `effort: low` | ✅ 實際型號 `claude-fable-5-1`,畫面顯示「未套用:thinking_off」 |
| 延續對話 | ✅ 第二輪只帶問題本身,答得出第一輪的內容 |
| 不合法的模型 ID | ✅ 400,訊息列出可用的別名與完整 ID 格式 |
| 伺服器端同步呼叫(`bridge_chat`,`X-Bridge-Wait: 20`) | ✅ 短題目直接回答;長題目 20 秒回工單 id,之後用 `op=job` 取回全文 |
| 串流 350 秒的工作 | ✅ 串流即時流動;280 秒時 Bridge 收尾、畫面標「不完整」並附工單 id;工作在 349 秒完成,用工單 id 取回全文 |
| 別的使用者查工單、撤銷別人的電腦 | ✅ 都是 404 |
| 撤銷電腦 | ✅ 之後的呼叫回 409;worker 下一次輪詢收到 401 後自行結束並提示重新連接 |

這一輪抓到、已修好的錯(每一條都補了測試):

| 症狀 | 原因 | 修法 |
|---|---|---|
| 綁定時 Bridge 回 500 | 平台自建表把 number 欄讀回成十進位字串(`"0"`、`"1790513946.341"`),`"0" > 0` 直接 TypeError;記憶體存放的測試看不到 | 存放層讀取的唯一出口依 schema 轉型 |
| 沒有空白的英數輸出(JSON、雜湊、長網址)到最後才一次出現 | worker 的遮罩為了不送出「可能是 email 前半」的字,扣住整段英數字串而且沒有上限 | email 帳號部分最多 64 字元,只扣最後 64 字;遮罩的比對規則同步加上限,已送出的仍保證是全文前綴 |
| 超過 240 秒的工作被截斷,卻標成「完整」 | worker 的單一工作上限寫死 240 秒,行程被砍後把已有的半截內容當成功回報 | 上限改為預設 1800 秒(`AIGO_BRIDGE_JOB_TIMEOUT_S`);被砍或沒收到結尾事件一律回報失敗 |
| 畫面上的「實際型號」是空的 | `local/*` 串流的標頭在 worker 回報型號之前就送出;Custom App 經 egress 的 `ctx.http.call` 拿不到回應標頭 | 串流的最後一個 chunk 與非串流回應的本體都帶 `x_bridge` |
| 沒設雲端金鑰時,409 仍建議「改用 anthropic/*」 | 提示寫死 | 只在 Bridge 真的設了對應金鑰時才提 |

平台面的觀察:

- **共用池租戶的配額**:每個 Hosted App 執行個體的記憶體上限是平台常數(這個租戶約 1.9 GB),
  租戶總量 8 GB,而且共用池租戶不能自設(`runtime-settings.resources` 回 403
  `RESOURCES_REQUIRE_DEDICATED_NODES`)。部署時新舊兩個執行個體要同時存在,
  租戶忙的時候部署會失敗(`exceeded quota: aigo-quota`),Custom App 的 action 也會回 503「App runner 暫時不可用」、
  回應帶 `quota_hint`。這不是程式問題,等配額鬆開再試。
- **有 worker 在線時,Bridge 不會縮到零**(S4 的結論在平台上也成立),等於長期佔一個執行個體的配額。
- 背景分頁的計時器會被瀏覽器節流,在背景分頁量到的前端時間不可信;時間以 worker 日誌與 Bridge 端為準。

### `auto`:本機與雲端主備(本機端到端 + 平台端到端)

**本機**(`tools/e2e_auto.py`):真 Bridge(記憶體存放)+ 真 worker(本人登入的 Claude Code)+
模擬 OpenRouter(`tools/mock_openrouter.py`,可以控制它故障),呼叫端是官方 `openai` 客戶端與
`clients/python/aigo_bridge.py`。9/9 通過:

| 項目 | 結果 |
|---|---|
| 沒選優先順序 | ✅ 409;openai SDK 以 `ConflictError` 呈現,`e.body["code"] == "priority_required"` |
| 本機優先、電腦沒開 | ✅ 雲端回答,`fallback.reason = no_worker_for_user` |
| 本機優先、電腦在線 | ✅ 本機回答(haiku、關 thinking)3.4 秒 |
| 串流(本機) | ✅ 最後一段帶 `x_bridge`,openai SDK 以 `chunk.model_extra` 讀得到 |
| 雲端優先、雲端正常 / 回 503 | ✅ 雲端回答 / 改用本機,`fallback.reason = provider_error` |
| 串流時雲端 503 | ✅ 出字前切到本機,內容完整、沒有混到兩邊 |
| 雲端回 400(請求錯誤) | ✅ 不切換,原樣回 `provider_bad_request` |
| 兩邊都失敗 | ✅ 回雲端的 429,訊息與 `X-Bridge-Fallback` 註明本機先失敗 |

**平台**:Bridge 部署成 Hosted App(冷啟動、平台自建表、**不設任何雲端金鑰**,雲端候選只有模型名稱),
新版範例 Custom App 發布後,以 action 與 session token 走真實路徑。17/17 通過:

| 項目 | 結果 |
|---|---|
| 還沒選 | ✅ `priority: null`,兩個選項都顯示目前不可用;`auto` 回 `priority_required` |
| 選本機優先 | ✅ 存進平台表,讀回的時間是數字 |
| 電腦沒開、雲端沒設 | ✅ 兩邊都失敗,訊息說明本機先失敗 |
| 綁好但還沒 `run` | ✅ 顯示離線(修正前會被當成在線,工單空等 30 秒才判定離線) |
| 本機優先、電腦在線 | ✅ 本機回答 |
| 雲端優先、雲端沒設 | ✅ 改用本機,`fallback.reason = provider_not_configured` |
| 瀏覽器路徑(session token) | ✅ 讀與改偏好(PUT)、`auto` 串流、CORS 允許 PUT 並公開 `X-Bridge-Priority` / `X-Bridge-Fallback` |
| 用量帳 | ✅ 記到 `ok`、`error`、`fallback` 三種 |
| 撤銷 | ✅ worker 收到 401 後以結束碼 0 結束(開機常駐不會無限重啟) |
| 發布閘門 | ✅ 四支 action 都是「貼上的區塊」,閘門認得區塊裡的字面 slug |

沒有驗到的:真的 OpenRouter(這輪刻意不用任何 AI 金鑰,雲端的轉送程式碼與前一版相同,並有單元測試);
新版前端的畫面點擊(瀏覽器擴充套件當時沒有連線;前端在平台上編譯與發布成功,瀏覽器走的 API 已用 session token 驗過)。

平台面的觀察:**刪除過的 Hosted App 的 slug 會被永久保留**,之後不能再用(平台說明是避免既有連結被別人接管)。
測試用的 slug 請取一次性的名字。

### S4 · worker 輪詢縮到零的 Bridge

量法:`spikes/cold-poll/probe.py`。Hosted App 為**冷啟動模式**(`always_on=false`,已讀回確認)。
先閒置一段時間再打一次,看實例是否換了;再每 5 秒輪詢 10 分鐘。

| 閒置多久後再打 | 結果 |
|---|---|
| 30 秒、1 分、2 分、4 分、8 分、**15 分** | 全部是同一個實例、沒有冷啟動,回應 54 – 140 ms |
| 每 5 秒輪詢 10 分鐘(119 次) | 0 錯誤、同一個實例,中位數 58 ms、p95 106 ms |

讀法:

- 冷啟動模式下,平台至少保留閒置實例 15 分鐘以上才縮到零(15 分鐘以上沒有再量)。
- worker 長輪詢每次最多 25 秒就再來一次,**只要有 worker 在線上,Bridge 就一直有流量、不會縮到零**。
  這不是開常駐,而是冷啟動模式本來的語意:有人在用就溫熱,所有 worker 都下線(例如夜間)後才縮到零。
- 部署新版後換上新實例,`/healthz` 第一次回應時 uptime 已 4 秒,代表平台在部署時就把實例拉起來了;
  「從零喚醒」的冷啟動秒數這一輪沒有量到。

### 由實測得出的決定

| 決定 | 依據 |
|---|---|
| worker **預設不帶任何 thinking / effort 參數**,照模型原本的行為;呼叫端可逐次指定模型(別名或完整 ID)、`reasoning_effort` / `reasoning.effort`(轉 `--effort`)、`reasoning.enabled=false` 或 `effort: "none"`(轉 `MAX_THINKING_TOKENS=0`) | S1b:關閉 thinking 有快有慢的取捨(haiku 快一倍但格式遵守變差),不該由 worker 替呼叫端決定 |
| worker 在 `message_stop` 就交付全文,`result` 到了再補 usage / cost | S1:兩者之間有約 1.3 秒的收尾摘要,另加 0.5 秒行程結束 |
| worker 永遠在**專用的空目錄**執行、加「不得提及附加資訊」條款、並對輸出做**確定性遮罩**(帳號 email、本機路徑) | Claude Code 會在每一輪附上環境快照與登入帳號 email,且沒有設定可以關掉;條款在測試中有效,遮罩是第二道防線 |
| Windows 上直接呼叫 `claude.exe`,不經 `claude.cmd` | `.cmd` 殼會重新解析引號,`--tools ""` 這類空字串參數有被吃掉的風險 |
| 不用 `--bare` | `--bare` 不讀訂閱登入 |
| **Bridge 必須留在 `*.ai-go.app` 網址,不能綁自訂網域** | S2:執行頁 CSP 只允許 `*.ai-go.app`;綁自訂網域後瀏覽器直連會被擋 |
| 瀏覽器不能直接打任何模型供應者 | 同上,CSP 不允許 |
| 同步等待上限**依呼叫路徑分開**:Bridge 預設 280 秒(Hosted 單一請求上限 300 秒,留 20 秒收尾);Custom App 的呼叫端區塊以請求標頭 `X-Bridge-Wait: 20` 要求較短的等待,超過就回 202 讓它之後查結果 | S3:30 秒硬牆只存在於 egress 這條路,撞牆時有兩種不同的失敗形狀,留 10 秒餘裕;S5:Hosted 本身是 300 秒 |
| 串流在 280 秒前由 Bridge 主動收尾並送 `[DONE]`,若工作還沒完成就在最後一個事件附上工單 id;呼叫端把「沒收到 `[DONE]`」視為不完整 | S5:300 秒一到連線直接被切,沒有錯誤狀態碼 |
| Custom App 的呼叫端區塊必須同時處理「`ctx.http.call` 回傳錯誤」與「action 被砍」兩種逾時 | S3 |
| 呼叫端區塊在 `ctx.http.call` 裡**寫死字面 slug** | 發布閘門只認得字面 slug;用常數傳入會被標成「動態 slug」而無法檢查授權 |
| 本機與雲端同時支援,以 `model: "auto"` 主備切換;**優先順序由每位使用者自己選,沒選之前 `auto` 回 `priority_required`**,Bridge 不設預設 | 兩個選項的代價不同(本機用使用者自己的方案額度、要電腦開著;雲端用組織的帳單),取捨應由使用者本人決定;預設值會讓使用者在不知情下用掉自己的額度或組織的預算 |
| 只有「換後端可能就會成功」的錯誤才切換;串流只在出字前切換 | 請求本身有問題換後端也一樣錯;出字後才切換會產生半段本機、半段雲端的回答 |
| 綁定不等於在線,要等 `run` 的第一次心跳 | 平台端到端:剛綁好還沒執行的電腦被當成在線,`auto` 要空等 30 秒才切換 |
| Bridge 的回應一律把實際型號與未套用的參數放進本體的 `x_bridge`(串流在最後一個 chunk) | 部署在平台上的端到端:`local/*` 串流的標頭送得比型號早;egress 的 `ctx.http.call` 拿不到回應標頭 |
| worker 的單一工作上限預設 1800 秒,被砍或沒有結尾事件都算失敗,絕不交出半截內容 | 同上:寫死 240 秒時,截斷的內容被標成「完整」 |
| worker 的擁有者以平台身分 `ctx.user_id` 為準,由 app 內的「連接我的電腦」流程綁定 | Server Action 拿得到的是 `ctx.user_id`,不是 email;身分來自平台而不是使用者自填 |
