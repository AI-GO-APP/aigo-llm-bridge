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
