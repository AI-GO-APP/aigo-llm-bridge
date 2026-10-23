# Windows 0.8.2 listener 安全驗收

狀態：已合併、發布及升級正式 Windows；受控重啟後真實 HTTPS 驗收通過。延續 [0.8.1 安全修補](2026-10-23-windows-081-security.md)。整合既有 main 的 core 0.8.1-mac.1，不另升共用版本；不操作 Mac／既有 Cloud 部署。

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
- 整合前／後 frozen 真訂閱各 7／7：text、兩來源 schema、兩來源工具提案、兩來源檔案 canary；各 8 項資料／隱私／成本檢查通過。每筆 usage.cost 以當次公開牌價及 receipt 核對；frozen controller spy 不具跨程序 argv 觀察能力，未將該項列入通過。
- [PR22](https://github.com/AI-GO-APP/aigo-llm-bridge/pull/22) 15 checks 通過，原生完整 renderer／更新 53／53、隔離 runner 電源 8／8。[原生 PR 收據](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39898818433)；[main 原生](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39899269643) 亦通過。

## 發布及正式驗收

- 合併來源 d6205e16d3f8469f7f8b29c594e90351234bc7fc；[publish 39899272979](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39899272979) 成功，[Windows 0.8.2](https://github.com/AI-GO-APP/aigo-llm-bridge/releases/tag/windows-installer-internal-v0.8.2) 公開，尚無 Authenticode。
- 六個公開附件匿名下載、hash／實包／簽章 policy 共 16／16。policy sequence 7、minimum 0.7.0、公鑰 fingerprint 9682eb28e5ab9020 均延續原渠道；nupkg SHA256 `0a3908486046ae4f1fa6f281cbc029372df4a3fcb42327335f300bbe8af298fd`。
- 原並行 Session 明確交接並停止修改服務後，核對其 0.7.1 source 程序的 path／PID，暫停接單、等零工作及零 child、SQLite backup，再停止該 idle Bridge，使用既有 0.8.1 native updater 真正升級至 0.8.2。未 kill by name，未碰其他 CLI。34 個 KEY row、193 筆 request、原設定全數保留；34 包含歷史已撤銷測試 KEY，不代表 34 個有效服務 KEY。
- 正式 0.8.2 四次真 HTTPS 通過：Codex text／schema、Claude schema／tools。成本分別 0.08594、0.08726、0.001705、0.003551 USD（當次 OpenRouter 牌價估值）；每次與 usage／receipt 核對。10 次 Claude argv 樣本無原文 marker／schema flag；profile 掃描無合成原文／完整 KEY。
- 受控 drain／shutdown／重啟 Bridge 後，同一 KEY 的真 HTTPS Codex PONG 通過，估值 0.058252 USD，差異來自該次 cache／usage。原 URL／device／配對 DPAPI／原 KEY／原 183 筆最初 baseline logs 仍一致。錯誤 KEY 拒絕、外部 management 不開放；臨時 KEY 撤銷，受保護測試 KEY 檔刪除。
- 重啟後核對實際 native owner、版本與來源，API／管理埠均拒絕第二個 SO_REUSEADDR bind，4／4 最終檢查通過。不重開電腦，不改使用者剪貼簿／電源／Claude 登入；未部署 Worker。

Jev／模型查詢已由原 Session 交接，另外進入 0.9 整合，不將 0.8.2 的舊 chat HTTPS 通過當成新端點通過。
