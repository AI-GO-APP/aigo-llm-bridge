# Windows 0.6.2：Cloud 相容與回執

本版新增不推論的 preflight、request ID 去重／deadline、文字工具提案與工具結果歷史。工具由呼叫端執行，Bridge 不開放本機 shell／MCP。未支援的參數仍明確回錯，串流仍不支援。

BYO 升級保留原裝置、URL、client KEY 與 transport secret。實測發現部署後重寫相同 secret 可能啟用舊 Worker，因此正常升級只部署程式；明確配對修復仍保留加密 pending 憑證與重試流程。

`GET /bridge/v1/receipts/<request UUID>` 使用原 Bearer KEY，只能讀取該 KEY 的請求。已完成結果在 RAM 有效期間可讀回；原文清除後只保留 token／成本等中繼資料。用於處理 Cloud 收到逾時但本機已完成的情況，不重新推論。整機失聯時無法保證立即取得部分 token 或已消耗成本。

驗證：94 項 Python、7 項 Worker 測試通過；Windows 原安裝更新、重啟、同 URL／KEY 的真實 Codex HTTPS 呼叫與牌價計算一致。原始 I/O 未出現在 Bridge profile 或新增 CLI 記錄，既有 Claude 程序保留。成本為 OpenRouter 牌價等值，並非訂閱的逐次現金扣款。

AI EA Cloud 已部署回執修正並使用正式成本帳；完整 AI EA 安裝版 UI 驗收仍另列，不能以 API 探針、來源版或本 Bridge 發布代替。macOS BYO 仍待實機驗證，本版只發布 Windows。
