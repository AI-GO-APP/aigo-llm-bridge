# OpenRouter 牌價換算

成功的推論回應會在標準 `usage.cost` 回傳 USD 金額，包含同步 chat 與 jobs 完成後的 `result.usage.cost`。金額是「CLI 用量依 OpenRouter 公開牌價換算的等值」，不是 OpenRouter 實際扣款，也不是 Claude／Codex 訂閱的剩餘額度。

```json
{"prompt_tokens":8568,"completion_tokens":23,"total_tokens":8591,"cost":0.017366}
```

這是 2026-10-22 合成內容實測的一次用量摘要。當時 `openai/gpt-6.1-sol` 一般輸入每百萬 token US$2、輸出 US$10，該次快取讀取為零：`8568 × 0.000002 + 23 × 0.00001 = 0.017366`。即時價格以 [公開 models API](https://openrouter.ai/api/v1/models) 為準；[模型價格頁](https://openrouter.ai/openai/gpt-6.1-sol)可供人工核對。

## 計算與更新

- 本機直接 GET 公開目錄，不需要 OpenRouter API key；不傳送 prompt、response、訂閱憑證或 Bridge key。
- 依登錄的實際 CLI native model 對應牌價，不依呼叫端自訂別名猜測。Codex 在啟動 ephemeral thread 時也會核對實際 model。無法精確對應或目錄沒有價格時，回 `503 pricing_unavailable`，不啟動推論。
- 公開價格快取 15 分鐘，寫入裝置資料目錄的 `openrouter-pricing.json`，重啟可沿用有效快取。內容只有公開 model ID、費率、來源與取得時間。快取過期且無法更新時回 503，不繼續使用過期價格。
- 以 Decimal 計算，依 CLI 回報 token 數區分一般輸入、已知快取讀取／寫入、輸出，再加上目錄中的每次請求費率；有 `overrides.min_prompt_tokens` 時套用對應階梯。推理 token 是輸出 token 的子集，不重複計費。
- CLI 沒有提供的快取分類無法精確還原；目錄沒有獨立快取費率時，以該類可取得的輸入費率換算。Codex 目前未提供快取寫入分類；Claude 已保留可取得的寫入與 1 小時拆分。這也是將金額標為牌價估算的原因。沒有必要 token 總數或明細不一致時回 `502 usage_unavailable`，不捏造 0 元。
- 不計 OpenRouter 儲值手續費、供應商訂閱月費或未實作的搜尋／工具費用；相關 request 仍依相容範圍明確拒絕。
- CLI token 用量包含 CLI 本身的指令上下文，不等於外部 messages 的字數；即使外部 prompt 很短，也可能有較多輸入 token。相同外部文字直接呼叫 OpenRouter 的用量不能視為必然相同。

本機同步成功回應另外提供以下 HTTP headers；新版 actor 的公開 Worker 只轉送這三項成本 headers，不開放任意本機 response header 外流。既有舊 actor 可能省略這些額外 headers；`usage.cost` body 與本機成本 metadata 不受影響。不能將這些 headers 當成所有既有安裝的必要欄位：

| Header | 意義 |
|---|---|
| `X-Bridge-Cost-Source` | 固定 `openrouter-list-price-estimate` |
| `X-Bridge-Pricing-Model` | 使用的 OpenRouter 牌價模型 ID |
| `X-Bridge-Pricing-Fetched-At` | 目錄取得時間，Unix 秒 |

jobs 的 result body 同樣包含 cost；其 GET 回應目前不附上述成本 headers。不增加非標準 body 欄位，也不捏造 OpenRouter 的 `cost_details.upstream_inference_cost`。

## Decisions 聚合與不完整用量

Decisions 每題獨立執行，先按各次實際模型、token 明細、階梯與 request 費率計價再加總。回應使用 input_tokens／output_tokens／cost。每次推論用量在答案驗證前保存，後續題目或輸出驗證失敗仍保留已知消耗。

收據新增 billing_status.complete、calls_started、calls_completed；未回報用量或模型身分不符時標示不完整，不捏造零元。明確指定的模型不自動換成小模型，不套用 Jev 牌價。詳見 [Decisions 指南](JEV-COMPATIBILITY.md)。

## 紀錄、更新與 Cloud 結算

SQLite metadata 新增 `cost_usd`、`pricing_model`、`pricing_fetched_ts`，啟動時自動遷移既有資料表，保留裝置身分及 key hash。這些欄位可隨既有 log 匯出及刪除；仍不保存 request／response 內容。

AI EA Cloud 原閘道會優先使用上游的 `usage.cost` 結算，再依既有契約移除成本才回桌面 client。本次隔離實測已確認金額可到達結算呼叫，但正式資料庫沒有執行這次測試。該閘道原本用 `p_estimated=false` 表示「上游已提供 cost」；若改接 Bridge，帳務還應另外記錄 provider 與成本來源，避免把牌價等值當成實際付費給 OpenRouter 的金額。

成本功能納入 0.3.4-byo 起的安裝包，並隨包附上本說明。更新時使用原 InstallRoot，保留原 data_dir；既有程序不會自動替換，需讓 Bridge 排空後重啟。公開 `/health` 回應的 `X-Bridge-Relay-Version: 0.3.4-relay` 識別外層 Worker，body 的 version 識別實際 actor；兩者可能不同，需分開驗收。不自動切換 actor 名稱或捨棄舊的待處理狀態。
