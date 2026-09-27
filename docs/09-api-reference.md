# 09 · API 參考

程式碼與測試以這份為準;改行為先改這份。怎麼用請先看 [05 · 呼叫端](05-callers.md),這份是逐條規格。

## 1. 驗證

每個請求擇一:

| 方式 | 標頭 | 誰用 |
|---|---|---|
| Source 金鑰 | `Authorization: Bearer <BRIDGE_KEY__<SOURCE> 的值>` | Server Action、其他 Hosted App |
| HMAC 簽章 | `X-Bridge-Source: <SOURCE>`、`X-Bridge-Timestamp: <unix 秒>`、`X-Bridge-Signature: sha256=<hex>`,簽 `"{timestamp}.{body 原文}"`,時間窗 ±300 秒 | 不想讓金鑰出現在請求裡的呼叫端 |
| Session token | `Authorization: Bearer <token>`(由 `/bridge/session` 發,最長 1 小時) | 瀏覽器 |

另外必帶 `X-Bridge-User: <平台使用者 id>`(Session token 已內含,不必帶)。
`local/*` 與 `auto` 用它配對使用者本人的 worker 與偏好;其他後端只用來記用量。

## 2. `POST /v1/chat/completions`

請求與回應都照 OpenAI Chat Completions 的形狀。`model` 決定後端:

| `model` | 後端 | 備註 |
|---|---|---|
| **`auto`** | 依使用者自己選的優先順序,在本機與雲端之間主備切換 | 見 §2.6。**建議的預設寫法** |
| `local/self`、`local/self:<別名或完整模型 ID>` | 呼叫者本人的 worker(本機 Claude Code) | 別名:haiku、sonnet、opus、fable;完整 ID 例 `local/self:claude-opus-5`。只支援文字與 JSON 輸出,見 §2.3。**沒有**指定他人電腦的寫法 |
| `openrouter/<vendor>/<model>` | OpenRouter `chat/completions`,**原樣轉送** | 例:`openrouter/anthropic/claude-sonnet-4.5` |
| 其他 `<vendor>/<model>` | 有 OpenRouter 金鑰就原樣交給 OpenRouter | 例:`openai/gpt-5.4-mini`。既有 OpenRouter 呼叫端的 model 寫法可以照用 |
| `anthropic/<model-id>` | Anthropic Messages API(官方 Python SDK) | 例:`anthropic/claude-opus-5`。OpenRouter 的點號寫法也收:`anthropic/claude-haiku-4.5` 會換成 `claude-haiku-4-5`。沒設 Anthropic 金鑰但有 OpenRouter 金鑰時,原樣交給 OpenRouter |
| `claude-<…>`(沒有前綴) | 同上 | 等同 `anthropic/claude-<…>` |
| 空字串或未帶 | `BRIDGE_DEFAULT_MODEL` | 未設定 = 400 |

非 `auto` 時,OpenRouter 專有欄位(`models`、`provider`、`usage`、`transforms`)照收不報錯:
轉送給 OpenRouter 時原樣保留,轉給其他後端時忽略。`auto` 時 `models` 另有意思,見 §2.6。

### 2.1 轉成 Anthropic Messages API 的規則

| OpenAI 欄位 | Anthropic | 規則 |
|---|---|---|
| `messages[].role = system`(任何位置) | 頂層 `system` | 依序以空行接起來。刻意不用「對話中途的 system 訊息」:只有部分模型支援,不支援的會 400 |
| `messages[].role = user / assistant` | `messages` | 內容是字串或 `[{type:text}, {type:image_url}]`;`image_url` 的 data URL 轉 base64 image、一般網址轉 url image |
| 最後一則是 `assistant`(預填) | — | **400**:目前世代模型不接受預填。請改用 `response_format` |
| `messages[].role = tool` / `assistant.tool_calls` | `tool_result` / `tool_use` | 見 2.2 |
| `max_tokens` / `max_completion_tokens` | `max_tokens` | 沒給:非串流 16000、串流 64000 |
| `stop`(字串或陣列) | `stop_sequences` | — |
| `temperature`、`top_p`、`top_k` | — | **目前世代模型(Opus 5/5.5、Sonnet 5、Opus 4.7/4.8、Fable 系列)會以 400 拒收**,這些模型一律丟棄並列在 `dropped`;較舊的模型照傳 |
| `reasoning_effort` / `reasoning` / `thinking` | `output_config.effort`、`thinking` | 見 §2.4。**沒指定就不送**,照模型原本的行為 |
| `response_format: {type: json_schema, json_schema: {schema}}` | `output_config.format`(JSON schema) | — |
| `response_format: {type: json_object}` | 系統提示加一句「只輸出一個 JSON 物件」 | 沒有 schema 就無法用結構化輸出強制 |
| `user` | `metadata.user_id` | 只放不可逆的雜湊,不放原值 |
| `stream_options.include_usage` | — | 串流最後一段附 `usage` |

**拒答後備(refusal fallback)**:模型為 `claude-opus-5` 或 `claude-fable-5-1` 時,預設帶
`fallbacks: "default"`(beta `server-side-fallback-2026-07-01`),被安全分類器拒答時由 Anthropic 端改用建議的模型重跑。
可用 `BRIDGE_ANTHROPIC_FALLBACKS=off` 關閉。這和 §2.6 的主備切換是兩件事。

**回應對照**:

| Anthropic | OpenAI |
|---|---|
| `stop_reason: end_turn / stop_sequence` | `finish_reason: stop` |
| `max_tokens` | `length` |
| `tool_use` | `tool_calls` |
| `refusal` | `content_filter`(另附 `refusal` 欄位與 `stop_details.category`) |
| `usage.input_tokens` + 快取讀寫 | `usage.prompt_tokens`(三者相加),另附 `prompt_tokens_details.cached_tokens` |
| `usage.output_tokens` | `usage.completion_tokens` |
| `thinking` 區塊 | 不輸出 |

串流:`content_block_delta.text_delta` → `choices[0].delta.content`;
`message_delta.stop_reason` → 最後一段的 `finish_reason`;錯誤在串流中途發生時送一個
`{"error": {...}}` 事件再結束。

### 2.2 工具呼叫

| 後端 | 支援 |
|---|---|
| `openrouter/*` | 原樣轉送 |
| `anthropic/*` | `tools[].function` → `tools[]`(`parameters` → `input_schema`);`tool_choice: auto / none` 照轉;`required` 與指定函式在 Fable 5.1、Opus 5.5 會被 Anthropic 以 400 拒收,Bridge 事先回 400 並說明改用 `auto` |
| `local/*` | **不支援**(worker 以無工具模式執行 Claude Code),帶 `tools` 回 400 |

`auto` 的兩側能力不同(本機不支援工具與圖片)。需要工具呼叫的請求請直接指定雲端模型,不要用 `auto`。

### 2.3 `local/self` 的額外規則

- 找不到 **擁有者 = 呼叫者** 且最近 90 秒內有心跳的 worker → `409 no_worker_for_user`。
  **不會改派給其他人的 worker**(`auto` 會改用雲端,那是同一位使用者的另一個後端)。
- `model` 可再指定模型:`local/self`(照 worker 上 Claude Code 的預設)、`local/self:haiku` 等別名,或完整 ID。
  **別名解析因帳號而異**(實測 `opus` 解析成 claude-opus-5,而非 Opus 5.5),要結果可預期就傳完整 ID。
- JSON 模式(`response_format`)下,若模型把 JSON 包在 ```json 外框裡,Bridge 會拿掉外框。
- 對話延續:帶 `X-Bridge-Session: <uuid>`,同一個 UUID 會在同一台 worker 上接續同一段 Claude Code 對話。

### 2.4 思考與 effort(三種寫法擇一或混用)

| 寫法 | 例 |
|---|---|
| OpenAI | `reasoning_effort: "low" \| "medium" \| "high" \| "xhigh" \| "max"`;`minimal` 視為 `low`,`none` 視為關閉思考 |
| OpenRouter | `reasoning: {"effort": …, "enabled": false, "max_tokens": 4096}` |
| Anthropic | `thinking: {"type": "disabled" \| "adaptive" \| "enabled", "budget_tokens": …}` |

**沒指定就不送任何思考參數**——照模型與 Claude Code 原本的行為(docs/01 S1b:關掉思考有快有慢的取捨,
不該由 Bridge 替呼叫端決定)。指定了但模型做不到的,不會送出,並列在 `dropped`:

| 情況 | 處理 |
|---|---|
| effort 用在不支援的模型(Haiku 4.5 等舊世代) | 不送,列 `reasoning_effort` |
| 關閉思考用在 Opus 5.5、Fable | 關不掉,列 `thinking_off`(local 由 worker 回報,同樣列出) |
| 關閉思考用在 Opus 5 且 effort 為 xhigh / max | 同上(Opus 5 只在 effort ≤ high 時接受關閉) |
| 開啟思考用在舊世代模型 | 轉成固定預算 `budget_tokens`(預設 4096,至少 1024,且小於 max_tokens;放不下就列 `thinking_on`) |

`local` 後端的對應:模型 → `--model`、effort → `--effort`、關閉思考 → `MAX_THINKING_TOKENS=0`。
OpenRouter 後端:三種寫法原樣轉送,由 OpenRouter 處理。

### 2.5 同步等待與串流長度

| 項目 | 規則 | 依據 |
|---|---|---|
| 同步呼叫最多等多久 | 預設 `BRIDGE_SYNC_TIMEOUT` = 280 秒;請求可帶 `X-Bridge-Wait: <秒>`(1–280)改短。等不到就回 `202 {"id"}`,工作繼續在背景做完,之後用 `GET /v1/jobs/{id}` 取 | Hosted 單一請求上限 300 秒(docs/01 S5) |
| **Custom App 的 Server Action 呼叫時** | **一定要帶 `X-Bridge-Wait: 20`** | egress 閘道的硬牆是 30 秒,而且撞牆時有兩種不同的失敗形狀(docs/01 S3) |
| 串流最長多久 | Bridge 在 280 秒時主動收尾:送一個 `{"error": {"code": "stream_timeout", "job_id": …}}` 事件,再送 `[DONE]` | 300 秒一到平台直接斷線、沒有錯誤狀態碼(docs/01 S5) |
| 呼叫端怎麼判斷串流完整 | 收到 `[DONE]` 且之前沒有 `error` 事件 | 同上 |

### 2.6 `auto`:本機與雲端主備

**優先順序由使用者自己選,Bridge 不設預設。**

1. 兩個候選:一個 `local/*`、一個雲端(`openrouter/*` 或 `anthropic/*`)。
   來源依序是請求的 `models`(例 `["local/self:sonnet", "openrouter/anthropic/claude-sonnet-4.5"]`,順序不影響)、
   Bridge 設定 `BRIDGE_AUTO_LOCAL`(預設 `local/self`)與 `BRIDGE_AUTO_CLOUD`。沒有雲端候選 = 只有本機。
2. 使用者的優先順序依「app(source)× 使用者」存在 Bridge(§5.1)。**還沒選過 → `409 priority_required`**,
   app 要在第一次使用時問使用者,不能替他決定。
3. 先試優先的那個。以下錯誤才改用另一個,其餘(請求本身有問題)原樣回報:

   | 側 | 會切換的錯誤代碼 |
   |---|---|
   | 本機 | `no_worker_for_user`、`worker_offline`、`worker_timeout`、`worker_failed`、`claude_exit`、`claude_error`、`claude_incomplete`、`claude_bad_output` |
   | 雲端 | `provider_not_configured`、`provider_unreachable`、`provider_rate_limited`、`provider_auth`、`provider_billing`、`provider_error` |

4. 串流:只在**送出任何內容之前**失敗才切換;已經開始出字就不換。
   本機優先時,Bridge 會等到第一段內容(或失敗)才回應標頭,所以 thinking 很長時,標頭會晚到。
5. 非同步(`X-Bridge-Async: true`):當下就要決定交給誰,所以依「現在可不可用」選(本機看有沒有在線的 worker,
   雲端看金鑰與模型有沒有設定)。
6. 同步等待超過上限(202)不算失敗,不會切換:工作仍在原本的後端進行。
7. 兩個都失敗:回最後一個錯誤,`message` 附上先前失敗的是誰、為什麼,標頭 `X-Bridge-Fallback` 同。
8. 需要使用者身分:沒有 `X-Bridge-User` 的呼叫(例如排程)不能用 `auto`,回 400 `user_required`。

### 2.7 回應的中繼資訊

| 欄位(本體 `x_bridge`) | 標頭 | 意思 |
|---|---|---|
| `served_by` | `X-Bridge-Served-By` | 實際回答的型號,本機是 `local:<型號>` |
| `dropped` | `X-Bridge-Dropped` | 指定了但模型做不到、沒有送出的參數 |
| `priority` | `X-Bridge-Priority` | `auto` 時,使用者選的優先(`local` / `cloud`) |
| `fallback` | `X-Bridge-Fallback`(`<先試的 model>:<錯誤代碼>`) | `auto` 改用備援時是 `{"from", "reason"}`,沒有則為 `null` |
| — | `X-Bridge-Job` | 這次呼叫對應的工單 id(本機或轉成工單時) |

- **非串流**:本體一律帶 `x_bridge`。Custom App 經 egress 的 `ctx.http.call` 拿不到回應標頭,要讀本體。
- **串流**:標頭在開始時就送出;本機後端要等 worker 做完才知道型號,所以最後一個 chunk 另帶 `model`(實際型號)
  與 `x_bridge`。瀏覽器可以讀這些標頭(CORS 已公開)。

## 3. 非同步與工單

帶 `X-Bridge-Async: true` → `202 {"id": "<job_id>", "status": "pending"}`。

`GET /v1/jobs/{id}`(同一個 source,而且是同一位使用者才看得到;別人一律 404)→
`{"id", "status": "pending|running|done|failed", "result": <chat.completion 形狀>|null, "error": {...}|null}`。

## 4. `POST /v1/responses`

接受 OpenAI Responses 形狀的最小子集(`instructions`、`input` 字串或訊息陣列、`max_output_tokens`、
`text.format`、`reasoning.effort`),轉成 §2 處理後,回 Responses 形狀(`output[].content[].text`、`output_text`、
`usage.input_tokens / output_tokens`)。只支援非串流。`model: "auto"` 同樣適用。

## 5. 使用者相關端點

### 5.1 `GET /bridge/preferences`、`PUT /bridge/preferences`(POST 亦可)

讀或設定這位使用者在這個 app 的優先順序。source 金鑰(帶 `X-Bridge-User`)或 session token 都可以。

```json
PUT {"priority": "local"}          // 或 "cloud"
→ {"priority": "local", "updated_at": 1790000000,
   "choices": [{"id": "local", "label": "我的電腦(Claude Code)", "model": "local/self", "available": true},
               {"id": "cloud", "label": "雲端(OpenRouter)", "model": "openrouter/…", "available": true}]}
```

`priority: null` 代表還沒選過。`available` 是**當下**狀態(本機:有沒有在線的 worker;雲端:金鑰與模型有沒有設定),
給畫面顯示用,不影響儲存。

### 5.2 `POST /bridge/session`

source 金鑰 → 短效 token。body `{"user": "<平台使用者 id>", "ttl": 3600}`(ttl 上限 3600)。
回 `{"token", "exp"}`。token 可以打 `/v1/*` 與 `/bridge/preferences`、`/bridge/workers`,
不能再換 token、不能產生綁定碼、不能打 worker 面。

### 5.3 綁定與電腦

| 端點 | 誰能呼叫 | 用途 |
|---|---|---|
| `POST /bridge/enrollments` | source 金鑰 + `X-Bridge-User`(**不接受 session token**) | 產生一次性綁定碼 `{"code", "expires_at", "bridge_url"}`,10 分鐘內有效 |
| `GET /bridge/workers` | source 金鑰 + 使用者,或 session token | 這位使用者的電腦清單 `{"workers": [{"id", "name", "os", "version", "status", "online", "last_seen_at"}]}` |
| `POST /bridge/workers/{id}/revoke` | 同上 | 撤銷自己的電腦;別人的回 404 |

綁定碼只能由 app 的伺服器端代表登入者發起,身分才來自平台而不是瀏覽器。

## 6. Worker 面

| 端點 | 用途 |
|---|---|
| `POST /worker/enroll` | 以一次性綁定碼換設備鑰匙(碼 10 分鐘內有效、用過即失效) |
| `POST /worker/claim` | 長輪詢,最多等 25 秒;只回擁有者 = 自己的工單,一次一筆,租約 60 秒 |
| `POST /worker/jobs/{id}/chunk` | 逐段文字(累積全文,冪等) |
| `POST /worker/jobs/{id}/result` | 全文、usage、cost、conversation session id |
| `POST /worker/jobs/{id}/fail` | 失敗原因 |
| `POST /worker/heartbeat` | 每 30 秒;帶 worker 版本與可用模型 |

設備鑰匙以 `Authorization: Bearer <device key>` 帶;Bridge 只存雜湊,可隨時撤銷(撤銷後回 401 `bad_device_key`)。

## 7. 錯誤

一律 `{"error": {"code": "<機器可讀>", "message": "<給人看的一句話>", "provider_status": <上游狀態碼或 null>}}`。
串流**開始之前**的錯誤回一般的 HTTP 錯誤;開始之後的錯誤以一個 `data: {"error": {...}}` 事件送出後結束。

| 狀態 | `code` | 意思與處理 |
|---|---|---|
| 400 | `bad_json`、`bad_request`、`model_required`、`unknown_model`、`unknown_provider` | 請求形狀或 model 寫法錯 |
| 400 | `bad_local_model`、`unsupported_local_target` | `local/self:` 後面不是別名或完整 ID;或試圖指定他人電腦 |
| 400 | `bad_auto_models`、`bad_priority`、`user_required` | `auto` 的候選不合法、優先順序不是 local / cloud、缺使用者身分 |
| 400 | `provider_bad_request`、`model_not_found` | 上游拒絕請求(附上游訊息前 300 字) |
| 400 | `bad_wait`、`stream_not_supported` | `X-Bridge-Wait` 不是秒數;`/v1/responses` 帶了 `stream` |
| 401 | `unauthorized`、`bad_signature` | 憑證不正確、簽章無效或過期 |
| 401 | `bad_device_key` | worker 的設備鑰匙無效或已撤銷 |
| 403 | `forbidden` | session token 做了它不能做的事 |
| 404 | `not_found` | 工單或電腦不存在,或不是你的 |
| 409 | **`priority_required`** | 使用者還沒選優先順序:畫面上問他,再 `PUT /bridge/preferences` |
| 409 | `no_worker_for_user` | 使用者的電腦沒有連線 |
| 413 | `request_too_large` | 請求太大 |
| 429 | `provider_rate_limited` | 上游限流,帶 `Retry-After` |
| 502 | `provider_auth`、`provider_billing` | **Bridge 自己的**雲端金鑰或帳戶有問題,不是呼叫端憑證錯 |
| 502 | `provider_error`、`provider_unreachable` | 上游暫時不可用 |
| 502 | `worker_offline`、`worker_timeout`、`worker_failed`、`claude_*` | 本機這一側在工作途中失敗 |
| 503 | `provider_not_configured`、`not_configured` | Bridge 沒有設定那個後端的金鑰;或還沒設任何 source 金鑰 |
| 503 | `store_unreachable`、`store_rate_limited`、`store_error` | 平台自建表暫時不可用(每分鐘 600 次的額度) |
| 503 | `no_backend_available` | `auto` 非同步時兩側當下都不可用 |
| — | `stream_timeout`(串流事件) | 串流到 280 秒上限;事件帶 `job_id`,之後用 `GET /v1/jobs/{id}` 取全文 |

上游 401 / 403 回 **502 `provider_auth`**,不原樣回 401,免得呼叫端以為自己的 source 金鑰錯了。
上游 400 類以外的錯誤不回原文(可能含金鑰片段或提示內容)。

## 8. 表(平台自建表,名稱前綴由 `BRIDGE_TABLE_PREFIX` 決定,預設 `biz_bridge_`)

| 表 | 用途 |
|---|---|
| `biz_bridge_jobs` | `local` 工單與非同步呼叫的狀態 |
| `biz_bridge_workers` | worker 名冊(擁有者、設備鑰匙雜湊、最後心跳、版本、可用模型、是否撤銷) |
| `biz_bridge_enrollments` | 一次性綁定碼(雜湊、擁有者、到期、是否使用) |
| `biz_bridge_usage` | 每次呼叫一列:source、使用者、後端、模型、token、成本、耗時、結果(`ok` / `error` / `fallback`) |
| `biz_bridge_prefs` | 使用者的優先順序(`auto` 用),一個 app × 使用者一筆 |

建表用 `tools/provision_tables.py`(預設只列計畫,`--apply` 才動手;兩步命名法:英文實體名建立、再改中文顯示名)。
查詢鍵欄位的實體名是 `lookup_key`(`key` 在部分 SQL 方言是保留字)。時間一律存 epoch 秒的 number 欄
(平台讀回來是十進位字串,存放層依 schema 轉回數字)。

提示與回應原文**預設不長期落表**。唯一的例外是 `local` 工單:Bridge 最多兩個實例,
worker 的長輪詢不一定打到收到請求的那一個,所以提示必須暫存在工單列上讓 worker 取得;
**工單完成或失敗時立即清除**(`request_json` 設為空)。`BRIDGE_STORE_PROMPTS=1` 才長期保存,供除錯。
