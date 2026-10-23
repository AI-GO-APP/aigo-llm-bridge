# 驗收與交付矩陣

R-23／D-29 的 Mac 公開 Worker 部署、全鏈合成推論與管理台證據修補見 [公開 API 上線收據](qa/2026-10-23-macos-public-api.md)。套件發布、已安裝來源與公開 Worker 驗證須分別記錄；不得以 401 路由探查或 health.online 代替真推論。

Mac **0.9.3-mac.1 已合併、發布、匿名下載校驗並完成正式安裝更新**；公開 Worker `0.9.0-relay` 的 Chat、Decisions 三題型、模型查詢／refresh／probe、jobs／receipt／去重與重啟驗收通過。原網址、裝置、owner Key 與容量保留；53 個安裝檔吻合公開 ZIP。此輪沒有發布 Windows，使用方應用程式與業務閾值未代驗。

Windows **0.9.2 已合併、發布並升級正式安裝**：改名、全機 runtime 唯一、native＋source、真標準使用者／TS session、明確停止後公開推論失敗、重啟後原 URL／KEY／資料與成本保留，見 [最終 Windows 收據](qa/2026-10-23-windows-machine-runtime.md)。Mac／Cloud 未在此輪部署。

Mac **0.9.1-mac.1 已合併、發布 source Release、公開下載安裝並完成 owner 更新／真 HTTPS 驗證**；最終 SHA、附件 hash、CI 與資料保留證據見 [Mac 發布收據](qa/2026-10-23-macos-release.md)。

產品改名的 repo／UI／文件、隔離畫面及舊更新來源連續性見 [改名 QA](qa/2026-10-23-product-rename.md)。Windows 新版安裝與發布以該收據的完成狀態為準。

Mac `0.8.1-mac.1` 的單元、原生 renderer、安裝更新與公開 HTTPS 證據另見 [Mac 同步 QA](qa/2026-10-23-macos-parity.md)；不發布 Mac release，不替代 Windows 安裝器測試。

Windows 0.9.0 已整合安全修補及 Jev／模型查詢，合併發布並升級正式安裝，真實本機三型、HTTPS chat、受控重啟、原 URL／KEY／資料／成本及雙埠獨占驗收通過。新公開 Jev／discovery 路徑尚未部署、實測 404，不能以既有 chat HTTPS 通過替代新端點驗收。[0.8.2 收據](qa/2026-10-23-windows-082-security.md)、[0.8.1 收據](qa/2026-10-23-windows-081-security.md)、[0.8.0 發布](qa/2026-10-23-windows-080-release.md)、[原 onboarding QA](qa/2026-10-23-windows-onboarding.md) 及 [鎖定 QA](qa/2026-10-23-windows-locked.md) 保留各階段歷史。

0.9 交接整合進度、付費 I/O／封裝／正式／Cloud 邊界另見 [本輪 Jev QA](qa/2026-10-23-windows-090-jev.md)。

本檔區分需求、測試與交付。source／單元測試、真實本機CLI、公開HTTPS、frozen安裝包、CI、正式已安裝、人工UI是不同證據，不能互相替代。沒有在本輪執行的測試不得標成新通過。

## 固定驗收案例

| 案例 | 對應需求／成功條件 | 適當驗證方式 |
|---|---|---|
| A-01 新安裝／部署 | R-01–03：無個人資料的包＋引導→自有Worker→固定endpoint、有效KEY、第三方訊息 | 乾淨profile，真實HTTPS，重複部署／重啟／更新前後hash與認證；不把撤銷所有測試KEY後的空profile當交付 |
| A-02 KEY生命週期 | R-04：新建兩來源預設、scope／RPM、輪替舊KEY失效、撤銷取消自有工作 | 管理API＋真HTTP models；frozen前端copy→OS clipboard精確讀回，測試KEY最後撤銷 |
| A-03 API相容 | R-05–06：指定model、預設／auto、非串流標準回應；unsupported參數明確400 | contract／service測試＋合成模型I/O，SDK不得偷偷加參數 |
| A-04 成本／工具 | R-07：數值cost、cache／reasoning不重算、格式失敗仍有已知billing、工具只提案 | pricing／tool_contract／receipt測試＋真CLI／外部呼叫獨立報告 |
| A-05 儲存隱私 | R-08：metadata欄位、CSV、篩選、刪除保留active，內容／完整KEY不落檔 | schema／掃描合成標記、CSV精確欄位、資料回讀 |
| A-06 CLI隔離 | R-09：不接續個人session、不改全域設定、不操作使用者視窗 | ephemeral／no persistence與供應商狀態檢查；不把模擬runner當真CLI證據 |
| A-07 WebView生命週期 | R-10：真native copy／Save／Cancel，按X後背景HTTP仍活，browser備援 | frozen probe＋實際桌面；自動Save選擇與人工點選分別記錄 |
| A-08 全頁視覺 | R-11：六頁＋modal＋Windows卡；淺深色、桌面／窄版，無整頁橫向溢出 | 實際render截圖＋DOM尺寸／keyboard／console；樣式文字存在不算視覺通過 |
| A-09 真安裝更新 | R-12：Setup→A→B、簽章／hash、排空、等待viewer退出、重啟、KEY／URL／資料不變 | `tools/verify_installer_update.py`與Windows runner；公開HTTPS更新另驗，不能只看loopback |
| A-10 文件可交接 | R-13：入口／七份產品文件／隨包文件／schema與API覆蓋／歷史區隔 | `tools/check_product_docs.py`、build_resources、人工語意對照；不以聊天摘要代替 |
| A-11 全機單實例 | R-21：不同 profile／port／安裝目錄／OS 使用者／TS session 不能多開；同 profile 喚回、拒絕不改 DB、正常／異常退出釋鎖；關窗與停止語意清楚 | 原子鎖及真 subprocess 競爭、隔離 HTTP、資料回讀；Mac [本輪 QA](qa/2026-10-23-macos-single-instance.md)，Windows [issue #20 收據](qa/2026-10-23-windows-machine-runtime.md)，須另驗真標準使用者與 TS session |
| A-12 Mac Release | R-22：現行包可匿名下載、hash／來源吻合、真下載安裝及原裝置升級／HTTPS通過 | [Mac 發布驗收](qa/2026-10-23-macos-release.md)、Mac release workflow／download smoke／既有 KEY／設定前後回讀 |

## 既有證據：0.7.2

- [2026-10-22 安裝器](qa/2026-10-22-windows-velopack-acceptance.md)、[2026-10-23 WebView與更新補正](qa/2026-10-23-windows-webview-acceptance.md)。
- 已發布 [Windows 0.7.2](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/windows-installer-internal-v0.7.2)，來源 a686833；142 Python passed／2 skipped，Node relay 9；隔離真Setup→A→B修正後兩輪39項通過；正式公開HTTPS更新13項通過，原URL／KEY／metadata及成本保留。
- Windows runner [原生驗收](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39818040291)及[公開政策再驗](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39820696732)。安裝包未具Authenticode。
- 後續實際桌面在隔離profile完成Save、中文檔名、Cancel、KEY預設表單及按X後背景HTTP200；CSV精確欄位、17／9 tokens、0.012345 USD回讀。瀏覽器備援CLI回0且出現Bridge視窗標題；瀏覽器畫面確認因Computer Use無法可靠判URL而停止，**不能稱該項畫面已通過**。詳細本輪紀錄見原報告補充段。

## 0.7.3 本輪

設計／文件／前端更新後的具體命令、畫面尺寸、版本、測試數與發布／正式升級結果記在 [0.7.3驗收報告](qa/2026-10-23-windows-design-docs.md)。0.7.3已發布並實際升級正式Windows，本機21項交付檢查通過。既有Worker在更新前後回1101，外網呼叫未通過；詳見該報告，不以本機結果取代外網證據。

## 維護閘門

```powershell
python tools/check_product_docs.py
python -m pytest desktop_bridge/tests packaging/windows/tests -q
node --test cloudflare/test/relay.test.js
node --test packaging/windows/tests/platform.test.js
python tools/lint_terms.py --require
```

Windows installer變更再跑真Setup→A→B與CI。純文件修改不要求重跑供應商推論；UI修改必須render，不能只加照著CSS內容寫的斷言。真LLM驗證使用合成內容、專用測試KEY，未知結果不盲重試。任何公開報告不含完整KEY、管理token、配對secret或原始使用者內容。

Mac的新UI／封裝／更新仍需Mac維護者獨立驗收；本輪不介入其作業。既有Mac報告不等於本次設計已在Mac通過。


64 併發的來源、Windows 安裝包及公開 Worker 驗收分層記錄於 [本次收據](qa/2026-10-23-windows-093-concurrency.md)。先前 626 筆本機 Codex 實測不替代新版正式 HTTPS 驗收；Claude 真實 64 負載及 >64 仍待驗證。
