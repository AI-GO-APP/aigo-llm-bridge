# Windows 0.9.3／core 0.9.4：64 併發交付

此為候選版收據；PR、CI、發布、原裝置更新及 Worker／HTTPS 驗收尚待完成。此頁在實際交付後補上可回讀的證據。

保留新版 Decisions、模型探索、成本核對及 Windows 全機單一 runtime。兩 provider 共用 64，Claude 真實 64 負載、長上下文及 >64 待驗。本次不發布 Mac。

## 候選原始碼驗證

- Windows 鎖定相依環境：Bridge 回歸 229 passed／13 skipped；新增後的併發測試檔 13 passed，含 64 混合 Chat／Decisions、Claude／Codex 共用容量及 Schema 等待取消。
- 工具及 Windows 更新測試 134 passed；Worker 13 passed；平台前端 3 passed。
- 文件覆蓋、品牌、22 詞禁字、版本與 diff whitespace 檢查通過。
- 原生 Setup／A→B、全機 runtime 與權限驗證將由拋棄 CI runner 執行，不修改正式裝置電源或登入。
