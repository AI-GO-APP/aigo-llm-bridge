# 產品文件入口

Mac 公開 Decisions／模型探索上線及本機／Worker／真實推論證據分層，見 [公開 API 收據](qa/2026-10-23-macos-public-api.md)。管理台可明確檢查公開路由，仍須另行執行會使用訂閱用量的推論測試。

產品名稱與改名相容性見 [BRANDING](BRANDING.md)：Local Token Buffet Bridge。

現行產品是 **BYO Cloudflare LLM Bridge**：安裝者自己的電腦、CLI 訂閱、Worker 與長效 client KEY。Windows 產品線使用 PyInstaller＋Velopack＋系統 WebView2。不需要外部租戶平台或 Supabase。文件、原始碼與驗收紀錄一同版控，AI agent 不應依靠聊天或本地記憶補出產品契約。

## 閱讀順序與權威範圍

| 文件 | 回答的問題 |
|---|---|
| [REQUIREMENTS](REQUIREMENTS.md) | 功能、非功能需求、邊界與驗收條件 |
| [ARCHITECTURE](ARCHITECTURE.md) | 現行元件、請求流程、信任邊界與程式碼地圖 |
| [SCHEMA](SCHEMA.md) | SQLite 全欄位、設定、RAM／檔案／憑證與遷移 |
| [API](API.md) | 現行外部端點、參數相容矩陣、錯誤與成本 |
| [DESIGN-SYSTEM](DESIGN-SYSTEM.md) | 前端 tokens、六頁版型、狀態、深淺色與平台適配 |
| [DECISIONS](DECISIONS.md) | 決策、理由、取捨、何時重訪 |
| [ACCEPTANCE](ACCEPTANCE.md) | 驗收矩陣、證據等級、已通過與待驗證項目 |
| [ONBOARDING](ONBOARDING.md) | 每台 Windows 的首次設定、CLI 授權、Worker、KEY、電源同意與還原 |
| [CI-CD](CI-CD.md) | 分平台 workflows、測試與發布閘門、權限及可重現建置 |
| [RELEASE](RELEASE.md) | 發布者操作、更新公告、強制更新、續期、故障處理及收據 |
| [SECURITY](SECURITY.md) | 現行信任邊界、原文不落地限制、schema 預算、依賴與安全更新 |

需求說明「應該做到什麼」；架構、資料與 API 文件說明實作契約；決策說明原因；驗收說明實際做到哪裡。衝突時不能自動把文件當成執行結果，也不能默默改需求來配合程式，須修正並留下紀錄。

## 安裝與使用

- [Windows 安裝與簽章更新](WINDOWS-INSTALL-UPDATE.md)、[管理台操作](P1-Windows-guide.md)。
- [Windows 首次安裝精靈](ONBOARDING.md) 將訂閱授權、Cloudflare CLI、一鍵／AI IDE 部署及插電權限納入安裝；通過狀態另看 QA。
- [自備 AI 方案接上 Bridge](SUBSCRIPTION-SETUP.md)：買完或兌換 Claude／ChatGPT 方案後，安裝 CLI、訂閱登入、確認就緒及 AI 助手提示詞。
- [BYO 首次部署](BYO-QUICKSTART.md)、[裝置／帳號生命週期](DEVICE-IDENTITY.md)、[安裝 agent prompt](AI-AGENT-SETUP.md)。
- [第三方串接訊息](THIRD-PARTY-INTEGRATION.md)、[牌價換算](OPENROUTER-PRICING.md)、[Cloud 呼叫端整合](AI-EA-CLOUD-BEST-PRACTICE.md)。
- [跨平台原始碼安裝](CROSS-PLATFORM-INSTALL.md)、[Mac 安裝／操作](MACOS-SETUP.md)、[Mac Release／更新](MACOS-RELEASE.md)。Windows Setup 與 Mac source ZIP 分流，驗收及發布各自負責。

- [模型查詢與 Jev Decisions](JEV-COMPATIBILITY.md)、[設計及歷史實測](JEV-COMPATIBILITY-PLAN.md)。新路徑需安裝者另授權更新 Worker，Windows Release 不自動部署。
- [跨平台原始碼安裝](CROSS-PLATFORM-INSTALL.md)。Mac 實機及 release 以 Mac 維護者的驗收文件為準；Windows 工作不替 Mac 發布或驗收。

## 維護約定

Mac source 的 [設定、常駐與來源更新](MACOS-SETUP.md) 及 [最新 Mac Release／公開 API 收據](qa/2026-10-24-macos-warm-cli-release.md)（[0.9.7 階段 0–2](qa/2026-10-24-macos-queue-release.md)）（[0.9.3 公開 API](qa/2026-10-23-macos-public-api.md)、[先前 Release](qa/2026-10-23-macos-release.md)、[parity QA](qa/2026-10-23-macos-parity.md) 為歷史證據）分別定義契約與獨立證據，不以 Windows 結果代替。

修改功能時，同一 PR 更新需求／API、資料字典、決策或設計文件中受影響的部分，並在 ACCEPTANCE 指向具體證據。新功能不能只留在聊天。文件的日期是維護日期，不是驗收通過證明。

執行 `python tools/check_product_docs.py` 檢查入口連結、SQLite 欄位／設定、API 頂層參數及設計 tokens 的文件覆蓋。它只能防止明顯漂移，不能代替語意審查或實機測試。CI 亦執行此檢查。Windows 安裝包隨附本組文件，未隨附的程式連結固定至該包的來源 commit。

## 歷史資料

[舊 README](../README-LEGACY.md) 與編號 01–13 的文件已改為停用導引頁，原文保留在 Git 歷史。`hosted/`、`worker/`、`desktop/` 的程式只供歷史相容維護，**不是現行產品的部署目標**；安裝與功能契約以本入口的現行 BYO 文件為準。


- [64 併發規格](CONCURRENCY.md)：共用容量、普通 API 呼叫、驗證證據及待驗範圍。

Mac 0.9.4-mac.1 整合與基本流程驗收另見 [Mac 併發交付](qa/2026-10-23-macos-concurrency.md)；Claude 真實 64 併發須以該收據的實際結果為準。

Mac #36 階段 0–2 的排隊、期限、固定 Decisions 驗證與量化門檻見 [效能計畫](PERFORMANCE-PLAN.md)，候選／正式狀態分層見 [本輪 QA](qa/2026-10-24-macos-queue-decisions.md)；warm CLI 另列 #39。

#39 已開始單次使用 warm CLI 試作，仍預設關閉；常駐零關閉／不得超過執行併發及後台開放條件見 [原型計畫](WARM-CLI-PLAN.md)，已驗與未驗見 [Mac 原型收據](qa/2026-10-24-macos-warm-cli-pilot.md)。

Mac 0.9.9 候選將 Codex 常駐接入正式 Chat／Decisions，提供容量卡與真 warm/cold receipt；owner 選擇 2/64，小量公開對照與發布狀態見 [本輪收據](qa/2026-10-24-macos-runtime-warm-pool.md)。預設仍零，Claude 仍按需啟動。
