# Windows P1 使用說明

目前產品決策為 **BYO Cloudflare only**。初次啟用先讀 [BYO 指南](BYO-QUICKSTART.md)，或把 [agent prompt](AI-AGENT-SETUP.md) 交給自己的 AI agent；發布方不提供共享入口。下列管理功能與 P1 相容範圍仍適用。

## 安裝與管理

解壓縮 `AIGO-LLM-Bridge-BYO-Windows.zip`，執行 `Install.cmd`。程式安裝在目前使用者的 `%LOCALAPPDATA%\AIGO LLM Bridge\versions\`，建立桌面、開始功能表的「LLM Bridge」捷徑，並設定登入 Windows 後縮小啟動。已包含 Python、Tk、TLS CA 與 schema 驗證套件。Claude Code／Codex 需另行安裝，並由使用者在原 CLI 登入訂閱帳號。

新版預設開啟瀏覽器管理台。關閉分頁後服務持續執行；再次開啟「LLM Bridge」捷徑可重新進入。要停止請按「結束 Bridge」並確認。自動啟動會在背景執行，可在「連線與設定」調整，使用 HKCU Run。P1 尚未提供 Windows Service、系統匣圖示或安裝移除器。以 `--native-ui` 啟動仍可使用舊版 Tkinter 視窗。

管理台分成總覽、API 金鑰、請求紀錄、模型管理、連線與設定，支援窄視窗。總覽分開顯示接單狀態、CLI 登入狀態與 Relay／Tunnel 狀態；設定公開網址不代表已經連線。管理台僅監聽 `127.0.0.1` 的獨立動態連接埠，使用本次啟動的管理憑證並檢查 Host／Origin；外部 API key 無法操作管理台。瀏覽器重整可保留該分頁的管理連線，Bridge 重啟後需從捷徑重新開啟。

更新前請先在原程式選擇「結束 Bridge」，待工作結束後執行新版安裝包；已在執行的舊程序不會被新捷徑自動取代。

資料在 `%LOCALAPPDATA%\AIGO LLM Bridge\data\`，與版本分開，更新安裝保留資料及舊版。API key 預設不會到期，重啟後仍有效。新電腦需自行登入 CLI 及配對獨立雲端入口；安裝包沒有任何個人帳號或 key。

「API 金鑰」可建立、命名、設定 Claude／Codex 來源、每分鐘上限，並撤銷或輪替。完整 key 只顯示一次，請保存到呼叫服務的 secret；遺失需輪替。撤銷／輪替舊 key 立即失效，介面也取消其未完成工作。

本機同時執行一筆、執行與排隊共最多九筆。CLI 狀態採唯讀檢查，不重新登入、不操作個人視窗、不接續個人 session、不改全域設定；取消只終止 Bridge 自己的程序群組。推論仍使用同一訂閱額度。

## 固定 HTTPS

每個安裝者在自己選定的 Cloudflare 帳戶，用 `tools/byo_setup.py plan`／`deploy` 建立裝置專屬 Worker。網址型式例如：

`https://your-worker.your-subdomain.workers.dev`

不需購買網域、固定 IP、路由器開 port 或 Cloudflare Tunnel。本機採出站 HTTPS 長輪詢。關機後網址仍存在，推論回 503；登入 Windows 並恢復連線後可用原網址、原 key 呼叫。保留 Worker、帳戶及路由名稱即可保留網址，不是每次重開隨機配發的 Quick Tunnel。

初次安裝需完成自己的配對。裝置 key 與外部 API key 分離，前者在自己的 Cloudflare secret 與本機 Windows DPAPI 保存，後者在資料庫僅保存 SHA-256 hash。每個 Worker 僅配對一個裝置設定檔，不複製給同時在線的兩台電腦。

新裝置依 [BYO 指南](BYO-QUICKSTART.md)部署自己的 Worker；已有自有 Worker 可用 `pair --url`。裝置 key 不提供給呼叫端。新增 API key 的雲端 hash 同步約需下一輪長輪詢，最多約 20 秒；舊 key 的本機撤銷即時生效。切換訂閱不改裝置 URL／client key，詳見 [授權生命週期](DEVICE-IDENTITY.md)。

網址本身無網域費，Workers／Durable Objects 仍受帳戶方案與用量上限約束；本次未購買或升級方案，沒有承諾無限免費。官方：[workers.dev](https://developers.cloudflare.com/workers/configuration/routing/workers-dev/)、[Durable Objects 計價](https://developers.cloudflare.com/durable-objects/platform/pricing/)。

## 既有 OpenRouter 服務改接

更換 Base URL、Bearer key 與可用模型。移除下表未支援參數。

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://your-worker.your-subdomain.workers.dev/api/v1",
    api_key=os.environ["LLM_BRIDGE_KEY"],
    timeout=95, max_retries=0,
)
result = client.chat.completions.create(
    model="openai/gpt-6-astra",
    messages=[{"role": "user", "content": "Reply briefly."}],
    stream=False,
)
print(result.choices[0].message.content)
```

HTTP 使用 `Authorization: Bearer <key>`、`Content-Type: application/json`。`HTTP-Referer`／`X-Title` 可保留，不作授權依據。本服務供伺服器呼叫，P1 沒有瀏覽器 CORS，不將長效 key 放進公開前端。

| 端點 | 行為 |
|---|---|
| `POST /api/v1/chat/completions` | 同步回標準 completion／error，不改成 202 工單。 |
| `GET /api/v1/models` | 此 key 可用模型的基本清單，不含 OpenRouter 完整價格目錄。 |
| `/v1/chat/completions`、`/v1/models` | 上述別名。 |
| `POST /bridge/v1/jobs` | 相同 inference body，回 202 與 id；Bridge 延伸端點。 |
| `GET /bridge/v1/jobs/{id}` | 同 key 查詢 queued／running／completed；完成的 result 為標準 completion。 |
| `GET /health` | 公開健康、近期裝置在線、版本；不含機器身分與訂閱帳號。 |

同步雲端請求最多等 90 秒，超過回 408；本機工作預設最多 180 秒，可調整。長工作或可能排隊時使用 jobs。同步 timeout 後原工作可能仍已執行，不要無限自動重試；P1 尚未提供 idempotency key。

jobs 結果只在本機 RAM 約保留 10 分鐘。過期 GET 以 HTTP 200 回工作描述、status=expired、error.code=410。重啟後結果遺失，未完成工作標為 interrupted，不保存原文來自動重播。其他 key 查詢工作回 404。

## 相容範圍

沿用 OpenRouter 支援欄位的名稱與型別，JSON object 欄位順序不作協定要求。省略 model 使用已保存的預設模型；新安裝預設 `openai/gpt-6-astra`（Codex），一般設定儲存不會改掉既有明確選擇。auto／openrouter/auto 是此預設模型的別名，沒有付費 fallback。預設登錄 `anthropic/claude-haiku-4.5` 與 `openai/gpt-6-astra`。登錄模型不代表訂閱一定有使用權。

| 參數／功能 | P1 |
|---|---|
| messages | 必填，1–100 則；最後一則非 system 訊息須為 user。 |
| system／developer | 文字指令映射 CLI，不建立持久 session。 |
| Claude 歷史 | 一則 user 加 system／developer，多輪明確 400。 |
| Codex 歷史 | user／assistant 多輪，使用 experimental ephemeral thread history injection。 |
| 圖片 | PNG／JPEG／WebP／GIF base64 data URL，每張 2 MB、整個 request 3 MB；遠端 URL、本機檔、音訊、影片、PDF 拒絕。 |
| response_format | text、json_object、object json_schema 子集；回傳前驗證 JSON／schema，失敗 502；外部 $ref／$dynamicRef 拒絕。 |
| reasoning.effort／reasoning_effort | low／medium／high／xhigh／max 映射 CLI，依模型能力；衝突 400。P0 實測 low，未窮舉所有模型 effort。 |
| stream | false／省略；true 明確 400。 |
| metadata／user／session_id | 驗證型別後丟棄，不寫 log、不作身分或持久對話。 |
| temperature、top_p、top_k、min_p、top_a、max_tokens、max_completion_tokens、stop、penalty、seed、logit_bias、logprobs 等 | 非 null 明確 400；官方可 null 的已知欄位可 null 表示未設定。 |
| tools、tool_choice、parallel_tool_calls、models、provider、plugins、cache 控制、prediction、service tier、trace、debug 等 | 無等價實作時明確 400，不啟用本機工具／路由／fallback。 |
| 訊息 name、tool role／tool result、未知欄位 | 明確 400。 |

成功回應含 id、object、created、實際登錄 model、system_fingerprint:null、choices、usage。usage 取 CLI 回報 token，`usage.cost` 依 OpenRouter 公開牌價換算 USD 等值；不是 OpenRouter 實際扣款或訂閱剩餘額度。目錄快取 15 分鐘，查無模型／過期且更新失敗時在推論前回 503；必要用量缺失時回 502。詳見 [成本與快取換算](OPENROUTER-PRICING.md)。錯誤範例：

```json
{"error":{"code":400,"message":"此參數目前沒有等價的 CLI 實作，請移除後重試。","metadata":{"error_type":"unsupported_parameter","parameter":"temperature"}}}
```

已實測官方 SDK 與簡單 chat；不是 OpenRouter 100% 相容。完整 43 欄位盤點見 P0 報告。CLI、experimental app-server 更新後需重跑實測。

## 紀錄與恢復

SQLite 僅記 request_id、key_id、已登錄 model／provider、時間、狀態、HTTP code、固定錯誤分類、耗時、bytes、tokens，以及牌價換算金額／模型／取得時間。介面可篩選、匯出最多 10,000 列 CSV、清除已結束紀錄，預設保存 30 天、顯示最近 500 列。

不保存 request／response 原文、附件、任意 metadata、Authorization、明文 key、原始 stderr／traceback。內容僅經 RAM pipe，不建立 request、圖片暫存檔。Claude 用 no-session-persistence；Codex 強制 ephemeral=true 並拒絕持久 thread path。個人 hooks、MCP、工具等僅對 Bridge 子程序停用。

這是應用程式與已檢查 CLI 儲存範圍的行為，不是 OS pagefile／記憶體傾印或供應商雲端的取證保證。DPAPI 綁定目前 Windows 帳號，更換帳號或重灌需重配對。備份資料目錄可保留 key hash、設定、中繼資料，不能還原原 key。

雲端 relay 的 request、authorization、result 僅在記憶體，未使用 Durable Object storage 保存內容，關閉 Worker observability。雲端部署或程序重啟可能中斷當下工作。P1 尚待高可用、多電腦、睡眠喚醒長測、簽章安裝包、完整畫面操作驗收與 macOS。
