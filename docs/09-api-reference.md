# 09 · API 參考(v0.1 草案)

> P2 實作中。這份是實作依據:程式碼與測試以這裡為準,改行為先改這份。

## 1. 驗證

每個請求擇一:

| 方式 | 標頭 | 誰用 |
|---|---|---|
| Source 金鑰 | `Authorization: Bearer <BRIDGE_KEY__<SOURCE>>` | Server Action、其他 Hosted App |
| HMAC 簽章 | `X-Bridge-Source: <SOURCE>`、`X-Bridge-Timestamp: <unix 秒>`、`X-Bridge-Signature: sha256=<hex>`,簽 `"{timestamp}.{body 原文}"`,時間窗 ±300 秒 | 不想讓金鑰出現在請求裡的呼叫端 |
| Session token | `Authorization: Bearer <token>`(由 `/bridge/session` 發,預設 1 小時) | 瀏覽器 |

另外必帶 `X-Bridge-User: <平台使用者 id>`(Session token 已內含,不必帶)。
`local/*` 用它配對 worker;其他後端只用來記用量。

## 2. `POST /v1/chat/completions`

請求與回應都照 OpenAI Chat Completions 的形狀。`model` 決定後端:

| `model` | 後端 | 備註 |
|---|---|---|
| `anthropic/<model-id>` | Anthropic Messages API(官方 Python SDK) | 例:`anthropic/claude-opus-5`。OpenRouter 的點號寫法也收:`anthropic/claude-haiku-4.5` 會換成 `claude-haiku-4-5`。沒設 Anthropic 金鑰但有 OpenRouter 金鑰時,原樣交給 OpenRouter |
| `claude-<…>`(沒有前綴) | 同上 | 等同 `anthropic/claude-<…>` |
| `openrouter/<vendor>/<model>` | OpenRouter `chat/completions`,**原樣轉送** | 例:`openrouter/anthropic/claude-haiku-4.5`(想明確走 OpenRouter 時用) |
| 其他 `<vendor>/<model>` | 有 OpenRouter 金鑰就原樣交給 OpenRouter | 例:`openai/gpt-5.4-mini`。讓既有 OpenRouter 呼叫端**只換 base URL 就能用** |
| `local/self`、`local/self:<haiku\|sonnet\|opus\|fable>` | 呼叫者本人的 worker(本機 Claude Code) | 只支援文字與 JSON 輸出,見 §2.3。**沒有**指定他人電腦的寫法 |
| 空字串或未帶 | `BRIDGE_DEFAULT_MODEL` | 未設定 = 400 |

同時接受 OpenRouter 專有欄位(`models`、`provider`、`usage`、`transforms`)而不報錯:
轉送給 OpenRouter 時原樣保留,轉給其他後端時忽略。

### 2.1 轉成 Anthropic Messages API 的規則

| OpenAI 欄位 | Anthropic | 規則 |
|---|---|---|
| `messages[].role = system`(任何位置) | 頂層 `system` | 依序以空行接起來。刻意不用「對話中途的 system 訊息」:只有部分模型支援,不支援的會 400 |
| `messages[].role = user / assistant` | `messages` | 內容是字串或 `[{type:text}, {type:image_url}]`;`image_url` 的 data URL 轉 base64 image、一般網址轉 url image |
| 最後一則是 `assistant`(預填) | — | **400**:目前世代模型不接受預填。請改用 `response_format` |
| `messages[].role = tool` / `assistant.tool_calls` | `tool_result` / `tool_use` | 見 2.2 |
| `max_tokens` / `max_completion_tokens` | `max_tokens` | 沒給:非串流 16000、串流 64000 |
| `stop`(字串或陣列) | `stop_sequences` | — |
| `temperature`、`top_p`、`top_k` | — | **目前世代模型(Opus 5/5.5、Sonnet 5、Opus 4.7/4.8、Fable 系列)會以 400 拒收**,這些模型一律丟棄,並在回應標頭 `X-Bridge-Dropped` 列出;較舊的模型照傳 |
| `reasoning_effort`(`low`/`medium`/`high`) | `output_config.effort` | 另接受 `xhigh`、`max`。不給就用模型預設 |
| `response_format: {type: json_schema, json_schema: {schema}}` | `output_config.format`(JSON schema) | — |
| `response_format: {type: json_object}` | 系統提示加一句「只輸出一個 JSON 物件」 | 沒有 schema 就無法用結構化輸出強制 |
| `user` | `metadata.user_id` | 只放不可逆的雜湊,不放原值 |
| `stream_options.include_usage` | — | 串流最後一段附 `usage` |

**拒答後備(refusal fallback)**:模型為 `claude-opus-5` 或 `claude-fable-5-1` 時,預設帶
`fallbacks: "default"`(beta `server-side-fallback-2026-07-01`),被安全分類器拒答時由 Anthropic 端改用建議的模型重跑。
可用 `BRIDGE_ANTHROPIC_FALLBACKS=off` 關閉。

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

### 2.3 `local/self` 的額外規則

- 找不到 **擁有者 = 呼叫者** 且最近 90 秒內有心跳的 worker → `409 {"error": {"code": "no_worker_for_user"}}`。
  不會改派給其他人的 worker。
- `model` 可再指定模型別名:`local/self`(worker 預設)、`local/self:haiku`、`local/self:sonnet`、`local/self:opus`。
- 對話延續:帶 `X-Bridge-Session: <uuid>`,同一個 UUID 會在同一台 worker 上接續同一段 Claude Code 對話。
- 同步等待上限 `BRIDGE_SYNC_TIMEOUT`(預設 20 秒),超過回 `202 {"job_id"}`,改用 `GET /v1/jobs/{id}` 取結果。

## 3. 非同步

帶 `X-Bridge-Async: true` → `202 {"id": "<job_id>", "status": "pending"}`。

`GET /v1/jobs/{id}`(同一個 source 或同一位使用者才看得到)→
`{"id", "status": "pending|running|done|failed", "result": <chat.completion 形狀>|null, "error": {...}|null}`。

## 4. `POST /v1/responses`

接受 OpenAI Responses 形狀的最小子集(`instructions`、`input` 字串或訊息陣列、`max_output_tokens`、
`text.format`),轉成 §2 處理後,回 Responses 形狀(`output[].content[].text`、`output_text`、`usage.input_tokens / output_tokens`)。

## 5. `POST /bridge/session`

source 金鑰 → 短效 token。body `{"user": "<平台使用者 id>", "ttl": 3600}`(ttl 上限 3600)。
回 `{"token", "exp"}`。token 只能打 `/v1/*`,不能再換 token、不能打 worker 面。

## 6. Worker 面

| 端點 | 用途 |
|---|---|
| `POST /worker/enroll` | 以 app 內發的一次性綁定碼換設備鑰匙(碼 10 分鐘內有效、用過即失效) |
| `POST /worker/claim` | 長輪詢,最多等 25 秒;只回擁有者 = 自己的工單,一次一筆,租約 60 秒 |
| `POST /worker/jobs/{id}/chunk` | 逐段文字(累積全文,冪等) |
| `POST /worker/jobs/{id}/result` | 全文、usage、cost、conversation session id |
| `POST /worker/jobs/{id}/fail` | 失敗原因 |
| `POST /worker/heartbeat` | 每 30 秒;帶 worker 版本與可用模型 |

設備鑰匙以 `Authorization: Bearer <device key>` 帶;Bridge 只存雜湊,可隨時撤銷。

## 7. 錯誤形狀

一律 `{"error": {"code": "<機器可讀>", "message": "<給人看的一句話>", "provider_status": <上游狀態碼或 null>}}`。

- 上游 400 類:附上游訊息前 300 字(通常是請求形狀的問題,開發者需要看到)
- 上游 401 / 403:回 **502 `provider_auth`**——那是 Bridge 自己的供應者金鑰有問題,不是呼叫端的憑證錯
- 其他上游錯誤:不回原文(可能含金鑰片段或提示內容),只回狀態碼與分類
- 上游 429:回 429 並帶 `Retry-After`
- 串流**開始之前**的錯誤回一般的 HTTP 錯誤;開始之後的錯誤以一個 `data: {"error": {...}}` 事件送出後結束

## 8. 表(平台自建表,名稱前綴由 `BRIDGE_TABLE_PREFIX` 決定,預設 `biz_bridge_`)

| 表 | 用途 |
|---|---|
| `biz_bridge_jobs` | `local` 工單與非同步呼叫的狀態 |
| `biz_bridge_workers` | worker 名冊(擁有者、設備鑰匙雜湊、最後心跳、版本、可用模型、是否撤銷) |
| `biz_bridge_enrollments` | 一次性綁定碼(雜湊、擁有者、到期、是否使用) |
| `biz_bridge_usage` | 每次呼叫一列:source、使用者、後端、模型、token、成本、耗時、結果 |

建表用 `tools/provision_tables.py`(預設只列計畫,`--apply` 才動手;兩步命名法:英文實體名建立、再改中文顯示名)。
查詢鍵欄位的實體名是 `lookup_key`(`key` 在部分 SQL 方言是保留字)。時間一律存 epoch 秒的 number 欄。

提示與回應原文**預設不長期落表**。唯一的例外是 `local` 工單:Bridge 最多兩個實例,
worker 的長輪詢不一定打到收到請求的那一個,所以提示必須暫存在工單列上讓 worker 取得;
**工單完成或失敗時立即清除**(`request_json` 設為空)。`BRIDGE_STORE_PROMPTS=1` 才長期保存,供除錯。
