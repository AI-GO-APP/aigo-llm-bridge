# spikes · P1 實測

P2 之後的設計有四個假設要先用實測確認。每個 spike 一個子目錄,量完把**數字與量法**寫回
[docs/01-architecture.md §5](../docs/01-architecture.md#5-實測依據);腳本留著供之後重跑,原始輸出不進 repo(`out/` 已忽略)。

| # | 要確認的事 | 做法 | 通過條件 | 不通過時的退路 |
|---|---|---|---|---|
| S1 | 本機 `claude -p` 的啟動時間、首 token 延遲、總時間 | `cli-latency/`:同一題各跑 N 次,量「行程啟動 → 第一個串流事件 → 第一段文字 → 結束」 | 首 token 中位數在互動可接受範圍(目標 < 8 秒) | 前端改顯示排隊狀態;worker 預熱 |
| S2 | 瀏覽器能否從 Custom App 執行頁直連 Bridge 的 SSE | `hosted-echo/` 部署成 Hosted App(假串流,不呼叫任何模型);Custom App 前端用短效 token 直連 | 跨來源 SSE 可收、token 驗證生效、斷線行為可預期 | 前端改為經 Server Action 輪詢工單表 |
| S3 | Server Action 經 egress 同步呼叫 Bridge 的實際可用秒數 | 同一個 Hosted App 提供「延遲 N 秒才回」的端點,從 action 逐步拉長 | 找出實際截斷點與錯誤形狀 | 同步模式只給短輸出,其餘一律非同步 |
| S4 | worker 固定間隔輪詢縮到零的 Bridge,冷啟動命中率與延遲 | 讓 Bridge 閒置到縮零後,模擬 worker 以 5 秒間隔輪詢 | 命中冷啟動時仍在租約時間內完成 | 評估常駐,或 worker 冷啟動重試 |

S2–S4 共用同一個 Hosted App(`hosted-echo/`),它**不呼叫任何 LLM**,只模擬串流與延遲,
所以部署到任何租戶都不會產生模型費用。

## 狀態

| # | 狀態 | 結論(細節見 docs/01 §5) |
|---|---|---|
| S1 | ✅ 完成 | haiku 首段文字 1.6 秒、sonnet 2.1 秒;必須關閉 extended thinking |
| S2 | 🟡 標頭層確認可行 | SSE 不被緩衝、CSP 允許 `*.ai-go.app`、CORS 預檢通過;瀏覽器實際操作待補 |
| S3 | ✅ 完成 | 29 秒內成功;30 秒硬牆,撞牆有兩種失敗形狀;同步上限定 20 秒 |
| S4 | ⏳ 量測中 | — |
