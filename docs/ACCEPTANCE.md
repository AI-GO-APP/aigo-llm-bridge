# 驗收與交付矩陣

Mac0.9.15程式／CI／公開ZIP／原機更新通過，但真API總99/116，64波47/64、RSS／FD亦未達；已回復0.9.12，4＋4／64／64與owner資料保留。不可視為正式放行；完整失敗／108筆已知用量及8筆unknown、結構風險#60見 [本輪收據](qa/2026-10-24-macos-auth-preflight.md)。

Mac後續 [優化研究](qa/2026-10-24-macos-optimization-probes.md)：24次原生Claude語意／格式通過、12次完整stream usage吻合、17次公開health通過、批次原型20項通過。去重候選total未改善，連線重用與batch尚未整合／部署；不把研究當成新版或完整#39放行。

Mac 0.9.12 後續以 owner 指定 **4＋4 常駐／64** 完成112/112真推論（公開96＋直連16）；公開64單波正確性通過，但p95=55.6066秒、38秒內38/64，完整warm速度門檻未過。Runtime外等待與Claude Decisions用量波動的分層證據見 [後續測試](qa/2026-10-24-macos-0912-staged-api.md)。測試Key全撤銷、原設定／Key保留，未重發產品版本。

Mac **0.9.12-mac.1 已合併、公開發布、匿名四附件／ZIP真安裝、原profile更新與同Key公開API驗收通過**。50個core及公開data／license吻合，原58筆Key rows／3把有效Key保留，唯一測試Key已撤銷；純Chat input3129→506，Decisions保留，原2/64/64及乾淨重啟通過。相容範圍、清理腳本負面紀錄與完整數據見 [本輪收據](qa/2026-10-24-macos-chat-minimal-release.md)。

Mac **0.9.8-mac.1 已合併、公開發布、匿名下載／ZIP 安裝及完成原安裝更新**。同一測試 Key 跨升級、公開 Chat／JSON／工具提案／去重與設定、裝置、owner Key、64/64 保留通過；少量 Chat／Decisions 延遲與完整發布證據見 [0.9.8 收據](qa/2026-10-24-macos-warm-cli-release.md)。warm pool 未啟用，#39 仍 open；不以小量測速代替 warm／64 併發門檻。

Mac **0.9.7-mac.1 階段 0–2 已合併、發布、匿名下載校驗及完成原安裝更新**。真訂閱 192/192、原 Worker HTTPS 64/64、公開 ZIP 實際安裝與全機互斥、升級後 Codex／Claude 三題型及成本收據通過；原設定、28 筆既有 Key rows 與 3 把有效 Key 保留。詳見 [完成收據](qa/2026-10-24-macos-queue-release.md)；warm CLI 仍為獨立 #39，Cloudflare 原免費配額未變。

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

Mac 0.9.4-mac.1 整合與基本流程驗收另見 [Mac 併發交付](qa/2026-10-23-macos-concurrency.md)；Claude 真實 64 併發須以該收據的實際結果為準。

Mac 0.9.5-mac.1：在 256 描述符上限下 64 個真實子程序經 HTTP 全數完成為必要回歸（未修正時約 40／64）。

0.9.7-mac.1／#36 的固定門檻見 [效能計畫](PERFORMANCE-PLAN.md)，source／自動化／合成／真訂閱／HTTPS／Release／正式安裝實際狀態見 [Mac 排隊 QA](qa/2026-10-24-macos-queue-decisions.md)。不得以候選基準或 401 代替正式公開 64 推論；warm CLI 另列 #39。

## #39 warm CLI 原型（未放行）

[Mac 原型收據](qa/2026-10-24-macos-warm-cli-pilot.md)區分 fake CLI 隔離、真 Codex 待命與小量對照，以及仍待完成的全量門檻。原型實測基線是 0.9.7-mac.1，後續 0.9.8 仍為 cold CLI；沒有管理 UI／常駐設定或 Windows warm 實機驗收。owner 的常駐零關閉及不得超過併發上限規則見 [計畫](WARM-CLI-PLAN.md)。

## Mac 0.9.8 發布與少量 API 延遲

owner 授權合併／發布 cold transport 與預設關閉的原型工具。交付與公開 LLM／Decisions 實測見 [本輪收據](qa/2026-10-24-macos-warm-cli-release.md)；這不表示 warm pool 或管理 UI 已放行。Windows installer 回歸保留真 clipboard 讀回，NULL owner 改用自有隱藏視窗；不發布 Windows 安裝包。

Mac 0.9.9 正式 API 的單次 Codex 常駐 operator 試驗／容量卡與後續公開開關對照狀態見 [本輪收據](qa/2026-10-24-macos-runtime-warm-pool.md)。預設零，Claude cold；完整 #39 放行另列，不將 UI／fake CLI 通過冒充真尖峰收益。

Mac 0.9.10-mac.1 已合併、公開發布、匿名下載／ZIP 安裝並更新原 profile。issue 46 的 goals／技能精簡令短 Chat／單題 Decisions 真實 input 分別減少 25.57%／24.76%；兩筆小樣本延遲未改善。原 2/64/64、Key、個人 config 保留，11 次 CLI 完整計量、臨時 Key 撤銷；剩餘內建上下文及診斷工具 cache=null 的 SQLite 補證見 [收據](qa/2026-10-24-macos-codex-context.md)。完整 issue 39 門檻仍獨立。

Mac 0.9.11-mac.1 的 D-42 已合併／公開發布／匿名下載 ZIP 安裝／原 profile 更新，16筆同題 HTTPS 對照全通過；input減少與延遲、cache／牌價折算差異分開揭露，2/64/64與owner Key保留。31次低量真推論含型別／工具注入、升級與續測；schema去重／thinking-off仍是研究候選，未正式採用。發布首次 close事件時序驗收失敗與同來源重跑、完整數據見 [本輪收據](qa/2026-10-24-macos-cli-token-release.md)。

D-43 的 [一般 LLM 結構性研究](qa/2026-10-24-macos-llm-structural-context.md)完成 12 次 credential-free mock 與 16 次小量原生訂閱測試；Codex 候選移除無關 agent 工具／context，500 caller-token 估算題 input 3,127→506。未整合、未發布、未取得同題 OpenRouter receipt；profile／共用容量／catalog 版本／完整品質與 API 門檻見 [計畫](LLM-CONTEXT-PLAN.md)。Decisions StructuredOutput 原樣保留，不能以本輪 Chat 成效冒稱已改正式服務或完成 near-parity。

R-25／D-44 的 Mac 0.9.12 純 Chat 整合、profile 共用容量、native config／wire／完整 caller 驗證及公開 ZIP／原安裝／API 分層狀態見 [收據](qa/2026-10-24-macos-chat-minimal-release.md)。Decisions StructuredOutput 不變；本項不代替完整 issue 39 效能放行或真 OpenRouter 同題對照。

R-26／D-46 的Mac0.9.13連線重用／batch8驗收見 [本輪收據](qa/2026-10-24-macos-relay-batch-release.md)。來源／fault回歸、真TLS／Cocoa、CI／包、原機更新及真公開A/B逐項分列；無模型模擬不能替代真64公開負載，#39／#46保留未達門檻。

0.9.13已發布但正式API後測51/52通過，一筆結果交付失敗，因此未跑64、原機回復0.9.12；不是完整放行。0.9.14 D-47修正的離線fault／真無推論傳輸及公開重驗分層見 [結果交付收據](qa/2026-10-24-macos-result-delivery.md)，保留失敗收據，不以改名或重送原推論掩蓋。

0.9.14正式20筆18有效，2筆Claude在推論Child前的預檢503；20筆傳輸全交付、零結果通道錯誤／補送，尚未進第二輪16／64。原機回復0.9.12。D-48／0.9.15 [metadata重新驗證QA](qa/2026-10-24-macos-auth-preflight.md)需保留失敗，另驗有界查詢／停止／未知用量與並發，不能把auth status Ready當作真推論或完整#39放行。

R-29／D-49 Mac0.9.16按owner要求以4＋4／32／32零推論簡易驗收交付；來源／CI／公開ZIP／原profile更新及回復逐項見 [本輪收據](qa/2026-10-24-macos-32-operator-release.md)。未要求或執行32／64真推論壓測，不改寫#39／#60歷史失敗／原完整門檻。
