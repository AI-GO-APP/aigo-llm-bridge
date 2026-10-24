# 模型查詢與 Jev 相容串接

同一個 BYO Worker 現在提供模型查詢與 OpenRouter Jev Decisions 格式，推論仍由本機 CLI 的訂閱執行，不需要新增 OpenRouter API key。沿用原裝置與 key，不因新增端點建立另一個 Worker。

## 查詢這把 key 可見的模型

所有端點帶 `Authorization: Bearer $LLM_BRIDGE_KEY`。origin 是本裝置的完整 Worker origin，不含 `/api/v1`。

| 方法及路徑 | 行為 |
|---|---|
| GET `/api/v1/models` 或 `/v1/models` | 標準模型列表，套用 key scope，排除目前已知不可用的模型 |
| GET `/bridge/v1/model-capabilities` | 模型、native ID、availability、目錄證據與 Decisions 驗證狀態 |
| POST `/bridge/v1/models/refresh`，body `{}` | 更新無推論能力資料 |
| POST `/bridge/v1/models/probe` | 固定合成內容的真實推論，body 為 `{"model":"實際模型ID","protocol":"decisions"}` 或 protocol 為 `chat` |

GET 與 refresh 不執行推論；probe 會消耗訂閱用量，使用既有佇列、限流及成本計算，不接受自訂 prompt。chat probe 核對 PONG；Decisions probe 回傳固定問題的 noul 答案。一次成功不保證下一次一定成功。

0.9.7-mac.1 的 Claude Decisions 對 repo 產生的固定結構使用 CLI 原生 JSON Schema 輸出，再由 Bridge 驗證型別及機率語意；state／題目／criteria 名稱仍只在 stdin／RAM。CLI 版本須支援 `--json-schema`／structured_output；格式失敗仍回 502 並保留已知成本，不重試。固定結構及原生輸出不保證機率校準相同。Claude 自有 Decisions 採 20 ms 冷啟動間距，受理與執行上限仍依 profile，等待計入期限。

同一登入下 refresh 最短 5 秒合併；正常快取 30 秒。登入世代改變立即失效，不因防重複探查而保留舊帳號證據。Windows 0.9.0 以 0.8.2 安全版為基礎，Decisions schema 定義及輸出同樣走受時間／記憶體／並行限制的隔離 validator。

`availability.state` 為 verified、unverified 或 unavailable，附 checked_at、expires_at、固定分類的 reason。catalog_listed 僅表示 CLI 有列出；Codex model/list 也可能是內建選單，不能證明訂閱權限。Claude 沒有等價的可靠訂閱模型列舉，因此列出登錄模型再以實際結果驗證。

目錄快取 30 秒，近期推論證據有效 60 秒，只在 RAM。CLI 執行檔、設定與可觀測登入檔 metadata 改變會使證據失效，不讀取或外傳 credential 內容。供應商端無法觀測的撤銷仍以實際呼叫為準。scope 每次重新套用；撤銷 key 後不能查詢。

新發現的 Codex native model 以 `openai/<native-id>` 列出，可直接呼叫，不改寫模型登錄或預設。明確設定的別名及對應優先。沒有可核對牌價的模型會回 pricing_unavailable；出現在目錄不代表必定可計價。

## 從 Jev 遷移

完整 URL 換成 `<origin>/api/alpha/decisions`，Authorization 換成 Bridge key，model 換成查詢並驗證的實際模型。保留 state、questions、criteria 與 provider.data_collection，不包成 messages，不需呼叫端增加 response_format。

例如已驗證可用的 Haiku 可用 `anthropic/claude-haiku-4.5`；Luna ID 以裝置回傳為準。它們是小模型建議，服務不會擅自替換指定模型。沒有執行 Jev 時，不用 typesafe/jev-1.13 偽裝同一模型。

```json
{
  "model": "anthropic/claude-haiku-4.5",
  "state": {"message": "請明天提供報價。"},
  "questions": {
    "needs_response": {"type": "noul", "instructions": "是否需要回覆？", "criteria": {"true": "需要提供或確認資訊", "false": "只需知道"}},
    "disposition": {"type": "choice", "instructions": "如何處理？", "criteria": {"reply": "回覆訊息", "act": "執行工作", "none": "不用處理"}},
    "tension": {"type": "score", "instructions": "有多緊繃？", "criteria": ["輕鬆", "平常", "有壓力", "不滿", "衝突"]}
  },
  "provider": {"data_collection": "deny"}
}
```

原解析程式仍讀 answers.needs_response.noul、answers.disposition.choice、answers.tension.score。另有 id、實際 Bridge model、執行 provider、usage.input_tokens、output_tokens、cost。不用 chat 的 choices 封裝，不回顯原始 request。noul 是 0–1 的機率而非 boolean；五級 score 從 0 到 4，可為小數。

這是一般 LLM 模擬。程式驗證分布，依官方公式計算 choice、score、confidence；不能保證與 Jev 相同答案、機率校準或速度，原有門檻需重新量測誤判率。

## 第一版範圍

- state 支援 string、object、array，每請求最多 100 題、body 3 MB。
- 題型為 noul、choice、score。instructions 必須存在，可為 string、object、array、null。
- choice 1–255 選項，score 2–10 個依序等級；criteria 描述保留結構化 JSON。同機率選原排列的第一個。
- noul criteria 可省略；提供時只能有 true／false 描述。user、session_id 上限 256 字，trace 是最多 16 組、8 KiB 的 object；接受後不傳模型、不持久保存。
- provider.data_collection=deny/allow 沿用相容語意，不代表強制執行訂閱供應商資料政策。其他未支援路由明確拒絕。
- 不接受 messages、stream、tools、取樣參數、圖片專屬欄位或其他題型，不宣告完整 OpenRouter／TypeSafe SDK 相容。
- 不做隱藏修復重試或跨模型 fallback，每題只看到共同 state 與該題，依既有單工作上限順序執行。

## 成本與失敗收據

每題都有實際推論，可能多次重讀 state。tokens 與 cost 加總所有實際呼叫；快取、推理 token、階梯與每次請求費率先逐次計算再加總。沒有額外路由小模型，也不拿 Jev 或未執行的小模型牌價代算。

usage.cost 延續 USD 的 OpenRouter 牌價估算，不是 OpenRouter 扣款，亦非訂閱費。[成本定義](OPENROUTER-PRICING.md)說明對應與 headers。無法核對模型或用量時明確失敗，不捏造金額。

首次 POST 設定唯一 UUID 的 X-AIEA-Request-Id，同一 key 可 GET `/bridge/v1/receipts/<UUID>`。billing.usage 是已知成本，billing_status 包含 complete、calls_started、calls_completed。第二題中斷時保留第一題消耗，complete=false 代表仍有未核對消耗，不能當作免費；答案驗證失敗也可能有成本。

結果只保留在 RAM 約 10 分鐘，之後收據仍有成本 metadata，不重播推論。不要對 408／斷線自動重試，可先查收據。公開標準 POST 約 90 秒，多題可能超時；長工作將相同 Decisions body POST 到 `/bridge/v1/jobs`，再 GET jobs。

## 安裝與升級驗收

依[安裝提示詞](AI-AGENT-SETUP.md)及[第三方驗收](THIRD-PARTY-INTEGRATION.md)操作。沿用 URL、key 與帳戶綁定；新路徑需 Worker、本機 Relay、Bridge 都更新，舊 Worker 可能回 404。文件不是部署授權；本次若要求不部署，只做本機測試，明列外部新路徑未驗證。

官方參考：[OpenRouter Decisions](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)、[TypeSafe confidence](https://docs.typesafe.ai/confidence)、[Codex model/list](https://learn.chatgpt.com/docs/app-server)。

## 歷史獨立分支本機驗證紀錄（0.7）

以下是交接來源分支 f9f6056 的歷史紀錄，不是整合主線或當前 Mac 的新驗收。0.9 Windows 整合狀態見 [本輪 QA](qa/2026-10-23-windows-090-jev.md)；Mac 依其獨立維護者的文件。

2026-10-23，0.7.0 原始碼在獨立 Windows profile 與 loopback HTTP 端點完成驗證，未連正式 Worker：

- Python 核心與工具共 207 passed、1 skipped；跳過項是 POSIX 專用鎖定測試。
- Worker 11 項測試通過，涵蓋新路徑、原 body／response 原樣轉送與不寫入 storage。
- 生成的 Python、PowerShell，以及解析後的 cURL URL／body 共 19 項 HTTP 範例驗證，已包含在上述 Python 數量內。
- 真實 Codex CLI 的唯讀 model/list 列出 7 個模型；沒有為查詢執行推論。
- 真實 openai/gpt-6-luna 三題請求 HTTP 200，15.966 秒，input_tokens 26,199、output_tokens 272，牌價估算 US$0.0027559。回傳模型與計價模型一致，收據 complete=true、3 started／3 completed，與回應成本相符。
- 臨時 key 已撤銷，隔離資料目錄已清除；只記錄上述中繼資料，沒有保存 prompt、答案或憑證。

同日，0.7.0 Windows 原生 ZIP 完成實際安裝驗收（不是從原始碼啟動服務）：

- 建置兩支原生 EXE；隔離 profile 的 CLI、HTTP、文件連結與安裝包不含個人憑證／資料庫檢查通過。
- 先暫停與排空原服務，備份 SQLite 及加密配對檔，再以 Install.ps1 覆蓋本機原生安裝。新 EXE 的雜湊與包內一致，/health 回報 0.7.0。
- 已安裝服務查得 8 個模型，capabilities 與 refresh 不觸發推論，Claude scope 的 key 不顯示 Codex 模型。
- 真實 anthropic/claude-haiku-4.5 三題（noul、choice、score）HTTP 200，36.096 秒，input_tokens 4,315、output_tokens 3,304，牌價估算 US$0.020835；response、計價 header 與收據模型一致，成本一致，complete=true、3 started／3 completed。
- 原生 setup 的含一次性 key 提示詞包含新端點、原 body、成本及重試限制；直接使用其中的 Decisions 範例完成真實 Haiku 推論。
- 再次覆蓋安裝後，同一驗收 key 仍可呼叫。原有 30 筆 key 雜湊與撤銷狀態、裝置身分、URL、Cloudflare 帳戶／Worker 綁定及加密配對檔逐項比對相同；驗收 key 最後撤銷且 HTTP 401。
- 上述輸入與回傳僅在記憶體處理，持久證據僅保留 allowlist 中繼資料。0.7.1 同步這些驗收文件與版本常數，推論程式與 0.7.0 相同。

正式 Worker 未部署，新公開 HTTPS 路徑尚未驗證；macOS 實機尚未驗證。模型機率的業務準確度與原有 Jev 門檻仍需依應用資料量測。


Decisions 與 Chat 共用每裝置 64 筆同時請求容量；各題仍依原順序獨立推論並加總真實成本。普通同步 API 可並行 POST，詳見 [併發規格](CONCURRENCY.md)。
