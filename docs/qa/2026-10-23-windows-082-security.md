# Windows 0.8.2 listener 安全驗收

狀態：候選實作／隔離驗收中，未發布。延續 [0.8.1 安全修補](2026-10-23-windows-081-security.md)。整合既有 main 的 core 0.8.1-mac.1，不另升共用版本；不操作 Mac／既有 Cloud 部署。

## 觸發與範圍

Windows 隔離 socket 實測兩個 SO_REUSEADDR listener 可綁同一 loopback 位址／埠。API nested Server 原先開啟 reuse，管理台也使用預設可重用的 HTTP server。另一個本機程序可能收到不確定的流量，影響 KEY／內容保密及可用性；不是外網未授權入侵實證。

只由 Windows 原生 entry 安裝 ExclusiveLoopbackServer adapter，對 API／管理埠先設 SO_EXCLUSIVEADDRUSE、關閉 SO_REUSEADDR；不改 stdlib 全域類別、source／Mac 入口、資料格式、價格公式、裝置或 KEY。占用時拒絕啟動，不覆蓋原有 listener。

## 放行條件

- 來源回歸、實際兩個 server 的同埠重綁負面測試。
- 封裝 Setup→A→B，實際 API／管理埠拒絕第二個 SO_REUSEADDR bind，原 URL／KEY／資料與 DPAPI 保留。
- 真實合成 HTTPS I/O、成本牌價與 receipt、內容不落地；正式重啟需先排除另一安裝流程，不能終止不明 owner。
- PR／main CI、公開資產及簽章 policy 回讀，正式 runtime 對照安裝版本後再聲明交付。

## 本機實測

- 整合 main d2e8a49 後 Python 254 passed／3 skipped；Worker／平台 Node 10 passed，文件及歷史 secrets 掃描通過。
- 第一輪 native 在測試 helper 漏傳 cfg 時中止，API 重綁已拒絕；第二輪因新 QA 尚未 tracked 被文件打包閘門拒絕。兩次失敗收據保留，未改正式程序；孤立測試 KEY 已撤銷。
- 修正 helper／追蹤文件後 Setup→A→B 35／35；整合版再驗 37／37，包含更新前後 API／管理雙埠拒絕重綁，URL／KEY digest／device／metadata cost／DPAPI／onboarding 保留，拒絕錯簽章、錯 feed、忙碌更新，最低版本門檻重啟後保留。僅本機略過 renderer，未改使用者剪貼簿或電源。
- 整合前 frozen 真訂閱 Codex／Claude 7／7：text、兩來源 schema、兩來源工具提案、兩來源檔案 canary；8 項資料／隱私／成本檢查通過。每筆 usage.cost 以當次公開牌價及 receipt 核對；frozen controller spy 不具跨程序 argv 觀察能力，未將該項列入通過。整合版真呼叫重驗中。
- [PR22](https://github.com/AI-GO-APP/aigo-llm-bridge/pull/22) CI 驗證中；正式切換仍受另一安裝流程的 owner 衝突限制，未終止它或操作 Claude Code 視窗。
