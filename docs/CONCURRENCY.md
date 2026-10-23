# 64 併發標準規格

2026-10-23 決定：Bridge 預設提供每裝置 64 筆同時推論。Claude 與 Codex 都採此預設；任一來源可使用全部 64 個槽，混合來源及 Jev Decisions 判斷請求合計仍為 64。同一裝置維持同一個 Worker、URL 與設定檔。

## 呼叫方式

以一般同步 JSON API 使用：直接並行呼叫 `POST /api/v1/chat/completions`，或 `POST /api/alpha/decisions`，每筆回傳各自的 completion／answers。呼叫端可使用 async/await、Promise.all 或 SDK 並行請求，HTTP connection pool 設為 64。標準整批呼叫不依賴 jobs API。

超出同時容量、key 頻率或訂閱額度時回 429。同步呼叫仍受約 90 秒時限限制；客戶端 timeout 建議 100 秒，408 或結果未知的斷線不自動重送。64 是同時執行容量，並非固定吞吐量或每筆延遲保證。

新建 key 預設 600 RPM，足以接納 64 筆突發請求；管理者可另設頻率限制。既有 key 的自訂 RPM 不自動改寫。

## 執行與轉接

- Runtime 預設 64 個 worker、64 筆未完成推論容量；每筆使用獨立 CLI 程序及記憶體 session。
- Schema 驗證維持最多 4 個隔離子程序、每次 3 秒預算；服務內部等待名額最多 30 秒，可取消，不要求呼叫端管理排程。
- 既有明確設定的 inference_workers 保留，可設 1–64；本次正式裝置更新後設為 64。
- Claude／Codex 共用推論容量，不按來源建立永久入口。
- 本機 Relay 分開使用 64 個推論轉送 worker 與 8 個控制 worker。
- Worker 原子受理最多 64 筆推論，另保留 8 筆 models／preflight／receipt 等控制請求；健康檢查不占推論槽。
- 標準範圍以上的 Runtime／測試工具設定目前拒絕啟用，避免將未驗證容量當成已支援規格。
- `/health` 提供 `max_concurrent_requests:64` 與 `shared_provider_capacity:true`。更新既有部署時須分別核對本機及 Worker actor；外層版本 header 不能證明舊 actor 已更新。

## macOS

Mac 自 0.9.5-mac.1 採同一規格。LaunchAgent 啟動的程序檔案描述符軟上限預設 256；64 個 CLI 子程序各占 3 個 pipe，再加上 API、Relay 與 Worker 連線會超過，實測只有約 40 筆能執行，其餘回 500。Bridge 在 POSIX 啟動時把軟上限提高到 4096（不超過硬上限，不修改系統設定）。回歸測試在 256 上限下以 64 個真實子程序經 HTTP 並行驗證。舊 Mac 設定檔保存的 `inference_workers` 需以 `mac_service.py workers --count 64` 明確更新。實機收據見 [Mac 64 併發](qa/2026-10-23-macos-concurrency.md)。

## 驗證狀態

先前 0.6.3 基礎的 Windows 隔離原始碼 Runtime 已用真實 Codex 訂閱完成單工至 64 併發、固定批量重測、判斷專用及主 LLM 專用測試。主模型為 `gpt-6-astra`，判斷模型為 `gpt-6-luna`；判斷測項每筆含 10 題與證據驗證。這是判斷 adapter 所使用的結構化 LLM 路徑，不是 Jev 原生模型校準測試。

64 併發已確認能完成；其吞吐與延遲隨輪次變動，部分判斷／混合測項超過 Cloud 首輪 38 秒預算。規格依本次決定固定為 64，不將單輪較快或較慢的數字宣稱為永久上限。詳細中繼資料見 [本機測試紀錄](concurrency-evidence/local-2026-10-23.json)。

Claude 的預設與排程同樣為 64，已以不消耗訂閱的並行測試驗證；Claude 64 筆真實訂閱吞吐仍待實測。新版整合與 Windows／公開 Worker 的交付證據另見 [發布驗收](qa/2026-10-23-windows-093-concurrency.md)。

## 待驗證項目

- **超過 64 併發**：另行授權後測試更高容量、各模型吞吐、CPU／記憶體、限流、逾時、正確率及持續負載；本輪停在 64，未啟動更高併發。
- Claude 64 併發的真實訂閱、取消與長時間負載。
- 更新安裝版及 Worker 後，經公開 HTTPS 的 64 筆標準 POST 與控制請求驗收。
- 64 併發下的長上下文、大型附件、長輸出及 Cloud deadline 整鏈。

Mac 0.9.4-mac.1 整合與基本流程驗收另見 [Mac 併發交付](qa/2026-10-23-macos-concurrency.md)；Claude 真實 64 併發須以該收據的實際結果為準。
