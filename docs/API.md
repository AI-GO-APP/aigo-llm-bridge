# 現行 API 與 OpenRouter 相容契約

本機管理 API：POST `/manage/check-public` body `{}` 明確執行無 Key、無推論的公開 route check；原 Host／Origin／管理 session 邊界不變，不能由 client key 操作。GET `/manage/state` 的 `public_endpoint` 與 `/manage/handoff` 包含 route evidence／時間及未驗說明。POST `/manage/test-connection` 新增選用 `protocol`（chat 預設、decisions），沿用 endpoint、provider、model、key 核對及單測試鎖；Decisions 使用固定 noul 合成內容，成功需答案型別／範圍、實際 model 與數值成本。Chat 亦核對實際模型及成本。404 指向同一 Worker 更新，不自動重試或部署。

Mac source 與 Windows 共用下列外部 API。Mac 管理台另提供 `/manage/macos-onboarding/{action}`（與 Windows 的 action 契約相同，平台授權除外）、`/manage/macos-console/browser` 及 `/manage/macos-update/apply`，均受原 loopback／Host／session 驗證保護。更新只使用安裝時記錄的來源路徑，不接受瀏覽器指定任意目錄。見 [Mac 設定](MACOS-SETUP.md)。

適用 `desktop_bridge/contract.py`、`tool_contract.py`、`service.py` 與 BYO relay。這是相容子集，不是 OpenRouter 全功能代理。JSON object key 排列不構成協定契約；不保證 OpenRouter 供應商產生的 id／指紋／回答值相同。

## 傳輸與授權

Base URL `https://<自己的-worker>.<自己的-subdomain>.workers.dev/api/v1`。帶 `Authorization: Bearer <client KEY>`、JSON POST 用 `Content-Type: application/json` 與 Content-Length。請求最多 3,000,000 bytes，不收 chunked body。`HTTP-Referer`／`X-Title` 可保留，無授權作用。不提供公網 CORS；KEY 放服務端 secret，不放公開網頁。

| 方法／路徑 | 成功與責任 |
|---|---|
| GET `/api/v1/models`、`/v1/models` | 200 `{object:"list",data:[...]}`，依 KEY provider scope／CLI 狀態篩選登錄及發現模型；不是 OpenRouter 完整價格／能力或訂閱權限證明。 |
| GET `/bridge/v1/model-capabilities` | scope 下的模型、native id、availability／checked_at／expires_at 與 Decisions 驗證證據；不推論。 |
| POST `/bridge/v1/models/refresh` | 空 object 更新能力資料，不推論；短時間重複刷新合併，參見下方快取規則。 |
| POST `/bridge/v1/models/probe` | 僅接受 model 與 protocol（chat／decisions）；固定合成輸入的真實推論，消耗用量／限流，沒有自訂 prompt。 |
| POST `/api/alpha/decisions` | Jev 相容 state／questions body；200 answers 與 input_tokens／output_tokens／cost，逐題隔離、依原順序呼叫。不是 Jev 模型或校準機率。 |
| POST `/api/v1/chat/completions`、`/v1/chat/completions` | 200 標準非串流 completion，或明確 error；不以 202 取代 completion。 |
| POST `/bridge/v1/jobs` | 同推論 body；202 `{id,status,created}`。Bridge 擴充，適合排隊／長工作。 |
| GET `/bridge/v1/jobs/{id}` | 同 KEY 查詢；有 RAM result 回標準 completion；結果過期描述為 expired／410，HTTP 本身仍可為 200。 |
| POST `/bridge/v1/preflight` | 驗 KEY／模型／參數／目前接單與容量，回 ready、model、subscription_verified:false、expires_in_s；不是實際訂閱或價格推論成功證明。 |
| GET `/bridge/v1/receipts/{uuid}` | 同 KEY 依 client request UUID 查執行與 billing metadata；原文過期後仍可取得已知計量。 |
| GET `/health` | 不需 KEY，公開健康／版本／接單；Worker 另有近期裝置在線判斷，不公開帳號或機器識別。 |

選用 `X-AIEA-Request-Id` UUID：本機以 KEY＋UUID 去重。相同 body 在 RAM 有 task 時回同一工作；內容不同 409 request_conflict；已受理但 RAM 不在時 409 request_already_processed，不重跑。不是通用 OpenRouter idempotency 規格。`X-Bridge-Deadline` 是 Unix 毫秒 deadline 的 Bridge 擴充，會縮短可用執行時間。

Decisions／模型查詢完整欄位與範例見 [專用指南](JEV-COMPATIBILITY.md)。Decisions 必填實際 model／state／questions，支援 noul、choice、score，最多 100 題；不接受 auto，不暗中換模型或重試。逐次按 CLI 回報實際模型核對後計價，再加總每次已計算成本，保留 cache／reasoning 細項；模型缺失／不符時回 502 並標記未知計量，不以請求模型捏造金額。失敗後同 KEY receipt 的 billing_status.complete／calls_started／calls_completed 區分已知成本與未完整計量，未知不是零。jobs／preflight 亦接受 Decisions body，去重包含 protocol 與問題／criteria 順序；trace／state／questions 不落地。

模型快取 30 秒、成功／失敗推論證據 60 秒；登入檔／CLI 設定變動使證據失效，執行中偵測變動即停止後續題目。GET／refresh 不建立推論 thread／turn，Codex 只用 model/list；Claude 僅登錄與登入／近期推論證據。相同登入下 refresh 最短 5 秒合併，避免持 key 者反覆啟動 CLI 探查；登入世代改變不等待此間隔。這些變更只更新 repo Worker 範本，既有 Cloud 端點需另外授權部署；不得以本機通過宣稱新 HTTPS 路徑已驗證。

## 頂層參數矩陣

| 欄位 | 必填／型別／規則 |
|---|---|
| messages | 必填 array，1–100；一般模式 role／content，工具模式可帶 tool history。詳見下節。 |
| model | 選填 string，不可 null；須已登錄或由 CLI 發現且 KEY 允許來源，推論前仍需有效牌價。省略、auto、openrouter/auto 使用保存的 default_model，不自動選模型或付費 fallback。 |
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
| power／power-admin | `consent=true`；只調整 AC 自動睡眠三項，一般權限優先／電源 ACL 不足才選用 UAC；背景讀回，不需要鎖定檢查或解除鎖定政策。 |
| restore-power／restore-power-admin | 一般還原原電源計畫／UAC 還原，後者需 consent=true；不變更 DC、螢幕、按鍵或任何鎖定登錄值。 |
| deploy | 明確 account_id 與 consent=true；重新驗帳戶後部署原 profile／Worker。 |
| create-key | 可選 label；回 id、一次 token、integration（含KEY的標準訊息）；預設來源全開，僅 hash 持久化。 |
| verify | key、model；背景真 HTTPS GET models＋單次合成 POST；RAM key不落盤；要求 PONG／有限非負數值 cost。 |
| finish | key_saved=true、handoff_copied=true、model；後端檢查當次 RAM proof、同 key_id／URL／交付模型與 native/provider 對應、KEY 未撤銷、來源登入、電源讀回與手動檢查確認，才存 completed_at。改交付模型／native 對應後必須重新 verify。 |

非同步接受回 `{ok:true,status:running}`，忙碌回 `{ok:false,code:busy}`；結果從 state 讀 job/status/action/code。狀態錯誤只回 operation_failed／permission_required，不回 CLI 原始錯誤、token 或模型內容。重新啟動後未完成者需貼回已保存 KEY 再明確 verify，不自動重播推論。詳細流程及環境限制見 [ONBOARDING](ONBOARDING.md)。

## 0.8.1 安全限制

Schema aggregate ≤256 KiB／8192 nodes／深度 24，不接受任何 $ref／$dynamicRef，包含 local ref；超限回 unsupported_parameter，不默默忽略。Schema 定義與輸出於自有子程序驗證，單次 3 秒、全機最多 4 個 validator；輸出超時 502，仍保留已發生用量與成本。Claude caller system／developer／schema 由 stdin 包裝，非原生 system role 或 CLI --json-schema；工具提案／structured output 仍須通過驗證。完整邊界見 [SECURITY](SECURITY.md)。


每裝置標準 64 筆同時推論，Claude／Codex、Chat／Decisions 共用。直接並行同步 POST；jobs 為可選進階擴充，標準整批呼叫不需要工單或輪詢。`GET /health` 回 `max_concurrent_requests` 與 `shared_provider_capacity:true`；本機反映實際設定，Worker 反映轉接容量。來源仍受 key RPM、訂閱及同步期限限制。詳見 [併發規格](CONCURRENCY.md)。

## 0.9.7-mac.1 候選：受理與排隊

本機 /health 與 /manage/state 的 max_concurrent_requests 是驗證＋排隊＋執行總受理數，另回 max_execution_workers、queued_requests（含驗證）、running_requests、shared_provider_capacity。Worker health 的 64 只代表外層上限。

以本機管理 token POST /manage/settings，body 僅含 `{"inference_workers":32,"inference_pending":64}` 可改容量；須 paused 且無未完成工作，1≤workers≤pending≤64。兩值與 live scheduler 一起更新。完整設定表單可帶原容量值，不能用混合更新改容量。

同步本機受理時取 min(90 秒、timeout_s、X-Bridge-Deadline)，包含驗證／排隊／輸出驗證；jobs 保留 timeout_s 並含排隊。queued timeout 為 408／calls_started=0，已完成程序清理才回 execution_state:terminated。本機斷線取消工作；公開 Worker 斷線沒有完整取消傳播，只依原 deadline 終止，不保證零用量。成功 body／計價不變；分段耗時只由本機 logs／CSV 取得。[放行門檻](PERFORMANCE-PLAN.md)。

終態 metadata 寫入失敗回 503 `metadata_unavailable`，釋放記憶體／受理名額且不回成功、不重送。先前已寫入的 billing 保留；DB 收據可能仍顯示非終態，直到後續恢復或重啟標為 interrupted，不能假造完整計量或以同 UUID 再推論。

## Mac 常駐池觀測與本機設定

0.9.9-mac.1 新增 loopback `/health` 的 `warm_pool`：resident_target、idle、starting、active、closing、quarantined、total、limit、peak、warm_hits、cold_starts、refill_failures、paused、unavailable、waiting_leases；只含數值／狀態，`warm_supported_providers` 目前 Mac 為 codex。每個 API receipt 的 `execution` 含本請求 warm_hits／cold_starts（多題 Decisions 加總），成功與失敗都保留，與 billing_status 分開；舊列當作未觀測零值，不代表歷史冷啟動已量測。

本機管理認證的 `/manage/settings` 可專用提交 `{inference_resident:2,inference_workers:64,inference_pending:64}`；必須 paused＋idle，整數 `0 ≤ resident ≤ workers ≤ pending ≤ 64`，workers 至少 1。省略 resident 的舊雙欄位請求保留原常駐數量；若新 workers 太小即拒絕，不暗中裁切。UI 使用同一 API。這不是公開推論參數，不增加 Worker 路由；一般 Chat／Decisions body 不變。

`warm_pool.created` 是 Codex 資源成功完成初始化的累計數；cold_starts 是租用冷啟動名額次數（也含 Claude），兩者均不是供應商 RPC 數或整棵程序樹程序數。

## Codex 輸入上下文（0.9.10-mac.1）

Chat／Decisions 的外部 body、模型、schema 與 receipt 計量不變。Bridge 專用 Codex 子程序停用 goals，並在每題 ephemeral thread 停用唯讀列出的技能，不改個人 CLI 設定；此查詢不是推論，納入 provider_setup_ms。技能清單結構無法確認時回 503 `codex_context_unavailable`，在 thread／turn 前停止；取消、逾時及 provider RPC 錯誤沿用既有分類。warm 仍只省初始化，不攤薄每題上下文。usage.prompt_tokens／input_tokens 包含 CLI 真實回報的全部輸入；剩餘工具／環境上下文尚未消除，cached_tokens 是其中子集，不可再加回總輸入。多題 Decisions 仍逐題、逐程序計量，不能當作單次推論或共享 thread。小樣本延遲與 mock token 估算的限制見 [驗收](qa/2026-10-24-macos-codex-context.md)。

## 純 Chat 執行模式（0.9.12-mac.1）

`receipt.execution` 另含已觀測的 `inference_profile`／`profile_reason`（固定值見 SCHEMA）；舊列省略兩欄，不冒充曾精簡。Mac 已驗 CLI binary／catalog／gpt-6.1-sol 的純文字 Chat 自動選 `codex-chat-minimal-v1`，不增加 caller 參數；其他模型／CLI／平台／外部 schema／tools／images 走 standard 並揭露原因。Decisions 一律 standard，StructuredOutput 與計量保持。`codex_profile_unavailable` 為 503：有效設定、profile 或版本在啟動／領取前無法確認，停止且不重送；不得把失敗當 near-parity 成功。[驗收](qa/2026-10-24-macos-chat-minimal-release.md)。

`warm_pool.idle_profiles` 按固定 profile 名稱提供 idle 數量；常駐合計仍為 resident_target。兩模式可用時交替分配（target=2 各 1、target=1 優先純 Chat），未驗 CLI 只保留 standard。沒有變更 caller 抽樣／輸出控制。兩個 profile 欄位是所選模式與原因，是否開始／完成及 billing 仍看原有獨立收據欄位；不是 OpenRouter 一比一用量保證。
