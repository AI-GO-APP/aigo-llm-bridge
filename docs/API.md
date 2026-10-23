# 現行 API 與 OpenRouter 相容契約

適用 `desktop_bridge/contract.py`、`tool_contract.py`、`service.py` 與 BYO relay。這是相容子集，不是 OpenRouter 全功能代理。JSON object key 排列不構成協定契約；不保證 OpenRouter 供應商產生的 id／指紋／回答值相同。

## 傳輸與授權

Base URL `https://<自己的-worker>.<自己的-subdomain>.workers.dev/api/v1`。帶 `Authorization: Bearer <client KEY>`、JSON POST 用 `Content-Type: application/json` 與 Content-Length。請求最多 3,000,000 bytes，不收 chunked body。`HTTP-Referer`／`X-Title` 可保留，無授權作用。不提供公網 CORS；KEY 放服務端 secret，不放公開網頁。

| 方法／路徑 | 成功與責任 |
|---|---|
| GET `/api/v1/models`、`/v1/models` | 200 `{object:"list",data:[...]}`，依 KEY provider scope 篩選已登錄模型；不是 OpenRouter 完整價格／能力目錄。 |
| POST `/api/v1/chat/completions`、`/v1/chat/completions` | 200 標準非串流 completion，或明確 error；不以 202 取代 completion。 |
| POST `/bridge/v1/jobs` | 同推論 body；202 `{id,status,created}`。Bridge 擴充，適合排隊／長工作。 |
| GET `/bridge/v1/jobs/{id}` | 同 KEY 查詢；有 RAM result 回標準 completion；結果過期描述為 expired／410，HTTP 本身仍可為 200。 |
| POST `/bridge/v1/preflight` | 驗 KEY／模型／參數／目前接單與容量，回 ready、model、subscription_verified:false、expires_in_s；不是實際訂閱或價格推論成功證明。 |
| GET `/bridge/v1/receipts/{uuid}` | 同 KEY 依 client request UUID 查執行與 billing metadata；原文過期後仍可取得已知計量。 |
| GET `/health` | 不需 KEY，公開健康／版本／接單；Worker 另有近期裝置在線判斷，不公開帳號或機器識別。 |

選用 `X-AIEA-Request-Id` UUID：本機以 KEY＋UUID 去重。相同 body 在 RAM 有 task 時回同一工作；內容不同 409 request_conflict；已受理但 RAM 不在時 409 request_already_processed，不重跑。不是通用 OpenRouter idempotency 規格。`X-Bridge-Deadline` 是 Unix 毫秒 deadline 的 Bridge 擴充，會縮短可用執行時間。

## 頂層參數矩陣

| 欄位 | 必填／型別／規則 |
|---|---|
| messages | 必填 array，1–100；一般模式 role／content，工具模式可帶 tool history。詳見下節。 |
| model | 選填 string，不可 null；須已登錄且 KEY 允許來源。省略、auto、openrouter/auto 使用保存的 default_model，不自動選模型或付費 fallback。 |
| stream | 選填 boolean，省略／false；true 回 400 unsupported_parameter。 |
| response_format | 選填 object：text、json_object、object 根 json_schema；校驗定義與實際輸出，格式失敗 502。工具提案模式不可另指定非 null response_format。 |
| reasoning、reasoning_effort | 選填 effort low／medium／high／xhigh／max；reasoning 只接受 effort。兩者衝突 400；CLI／模型不支援時不保證可用。 |
| user、session_id | 選填 string，最多 256 字；驗證後丟棄，不作身分或持久對話。 |
| metadata | 選填 object，最多16組，key≤64字、string value≤512字；驗證後丟棄，不入 log。 |
| provider | 選填 null／object；僅 data_collection:"deny"／"allow" 可作相容 metadata。不是 OpenRouter 路由或供應商政策保證；order 等欄位回 400。 |
| tools | 選填 1–256 個 function 定義，開啟工具提案 adapter；不執行本機 shell／MCP。 |
| tool_choice | 搭配 tools：auto、none、required，或指定 function name；沒有 tools 不接受。 |
| parallel_tool_calls | 搭配 tools 為 boolean；指提案可多筆，不表示 Bridge 執行工具。沒有 tools 時只有 null 可視為未設。 |
| temperature、top_p、top_k、min_p、top_a | 不提供等價抽樣控制；非 null 回 400。 |
| max_tokens、max_completion_tokens、stop | 非 null 回 400，不偷偷轉成非等價 CLI output 上限。 |
| frequency_penalty、presence_penalty、repetition_penalty、seed | 非 null 回 400。 |
| logit_bias、logprobs、top_logprobs | 非 null 回 400。 |
| prediction、service_tier、route、stream_options | 非 null 回 400。 |
| prompt_cache_key、prompt_cache_options | 非 null 回 400；不提供呼叫端 cache 控制。 |
| cache_control、debug、deferred_tools、image_config、modalities、models、plugins、stop_server_tools_when、trace | 明確不支援，包含 null 不視為已實作。 |
| 其他未知欄位 | 400 unsupported_parameter，parameter 為 unknown_field；不回顯未知原值。 |

上述允許 null 的未支援欄位以 `contract.NULLABLE_UNSUPPORTED` 為正本，null 只代表未設定。不得因 SDK 附加了欄位就默默忽略非 null 語意。

## 訊息與工具

一般訊息允許 system／developer 文字指令、user／assistant 歷史；最後一則非 system 須 user。Claude 一般模式只收單一 user turn，Codex 可收多輪 ephemeral history。message.name 與未知訊息欄位拒絕。

content 為 string 或非空 parts；支援 text 及 PNG／JPEG／WebP／GIF base64 data image_url，每張解碼≤2 MB，整個請求≤3 MB。不下載遠端 URL、不讀呼叫者本機檔、不寫圖片暫存檔；音訊／影片／PDF 拒絕。system／developer／assistant 歷史僅文字。image detail 可 auto／low／high；Claude 僅 auto。

工具模式接受文字歷史、assistant.tool_calls 與對應 tool_call_id 的 tool result；未完成或不存在的 call id 拒絕。function 名稱唯一且 schema 根為 object，不接受 $ref／$dynamicRef。adapter 將結構化輸出轉成 OpenRouter 風格 tool_calls，再以原函式 schema 驗 arguments；失敗 502 invalid_tool_proposal。執行權與工具結果由呼叫端決定。此模式不是 CLI 原生完整 function calling，也不支援圖像與 tools 混用。

## 回應與計量

成功包含 id（gen- 前綴）、object:"chat.completion"、created、實際登錄 model、system_fingerprint:null、choices 與 usage。一般 message 是 assistant＋content；工具提案可含 tool_calls，finish_reason="tool_calls"；一般正常化 stop／length／content_filter。

usage 含 prompt_tokens、completion_tokens、total_tokens、數值型 cost；可含 prompt_tokens_details 的 cached_tokens／cache_write_tokens 及 completion_tokens_details.reasoning_tokens。cost 是實際 CLI 模型對應 OpenRouter 公開牌價 USD 等值，非訂閱實際扣款／餘額。推理 tokens 屬輸出子集，不加算兩次。回應成本來源 header 與失敗處理見 [OPENROUTER-PRICING](OPENROUTER-PRICING.md)。

錯誤外形：`{"error":{"code":400,"message":"...","metadata":{"error_type":"unsupported_parameter","parameter":"temperature"}}}`。code 為數值 HTTP 狀態；message 不含原始 stderr／prompt／憑證。

| HTTP | 常見分類與呼叫端行為 |
|---|---|
| 400／413／415 | invalid_request、unsupported_parameter、model_not_found、request_too_large；修正輸入，勿原樣重試。 |
| 401／403 | authentication／forbidden；檢查 KEY／scope，不要另建 Worker。 |
| 408 | timeout；執行狀態不確定時查 receipt，不能盲目重複計量。 |
| 409 | request_conflict／request_already_processed；依原 UUID 查回執。 |
| 429 | queue_full／rate_limit_exceeded；遵守 Retry-After，評估原工作是否已受理。 |
| 499 | cancelled；KEY 撤銷或明確取消。 |
| 502 | invalid_provider_response／invalid_structured_output／invalid_tool_proposal／usage_unavailable 等；可能已有可計量用量，查 receipt。 |
| 503 | device_paused、離線、pricing_unavailable 等；缺有效價格時在推論前拒絕。 |

Worker 同步等待上限約 90 秒，SDK 建議 timeout 95–100 秒、停用自動重試；長工作用 jobs。本文不把所有錯誤都視為可免費重試。

## 本機管理 API

`GET /manage/state`、`/manage/logs`、`/manage/export`、`/manage/handoff`；POST `/manage/keys/create|rotate|revoke`、`/manage/accepting`、`/manage/auth`、`/manage/settings`、`/manage/pair`、`/manage/logs/clear`、`/manage/test-connection`、`/manage/tunnel/start|stop`、`/manage/shutdown`。只允許本機管理 token；Windows 包另加 `/manage/windows-update/*`。這些不是外部 OpenRouter 契約，不能轉到 Worker 或用 client KEY 呼叫。

Windows 0.8.0 候選另加 `state.windows_onboarding` 及 POST `/manage/windows-onboarding/<action>`：

| action | 請求／回傳 |
|---|---|
| refresh | `{}`；背景重新查詢兩來源登入與 Cloudflare allowlist accounts。 |
| open／opened | `{}`；CLI 請求手動開啟精靈／前端確認已開啟，一次性 RAM 旗標；不清除完成紀錄或重跑日常設定。 |
| login | `provider=codex/claude/cloudflare`；只啟動官方授權，ready 者沿用；來源有 active request 時拒絕。 |
| cli-paths | codex_path／claude_path 字串，空白自動偵測；原生執行檔驗證後只保存 Bridge 設定。 |
| prompt | `{}`；回傳不含憑證的 AI IDE 協作 prompt，帶原安裝位置／data-dir。 |
| power／power-admin | `consent=true, lock_checks_acknowledged=true`；一般套用／明確 UAC 提權；背景讀回，無權／政策限制不得通過。 |
| restore-power／restore-power-admin | 一般還原／UAC 還原，後者需 consent=true；不變更 DC 或管理員 HKCU。 |
| deploy | 明確 account_id 與 consent=true；重新驗帳戶後部署原 profile／Worker。 |
| create-key | 可選 label；回 id、一次 token、integration（含KEY的標準訊息）；預設來源全開，僅 hash 持久化。 |
| verify | key、model；背景真 HTTPS GET models＋單次合成 POST；RAM key不落盤；要求 PONG／有限非負數值 cost。 |
| finish | key_saved=true、handoff_copied=true、model；後端檢查當次 RAM proof、同 key_id／URL／交付模型與 native/provider 對應、KEY 未撤銷、來源登入、電源讀回與手動檢查確認，才存 completed_at。改交付模型／native 對應後必須重新 verify。 |

非同步接受回 `{ok:true,status:running}`，忙碌回 `{ok:false,code:busy}`；結果從 state 讀 job/status/action/code。狀態錯誤只回 operation_failed／permission_required，不回 CLI 原始錯誤、token 或模型內容。重新啟動後未完成者需貼回已保存 KEY 再明確 verify，不自動重播推論。詳細流程及環境限制見 [ONBOARDING](ONBOARDING.md)。
