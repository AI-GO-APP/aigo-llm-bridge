# 產品需求

基準：Windows 安裝器 0.7.3 設計／文件更新。既有 0.7.2 安裝與公開更新結果見 [ACCEPTANCE](ACCEPTANCE.md)。本檔列契約，通過狀態由驗收文件另行記錄。

## 目標與角色

進階安裝者在自己的 Windows 電腦安裝 Bridge，以既有 Claude Code／Codex 訂閱提供固定 HTTPS 入口給持有其 KEY 的服務。呼叫端原用 OpenRouter 時，以更換 base URL、KEY、模型及移除不支援參數的成本接入。發布者提供軟體及更新，安裝者自行部署、管理自己的 Cloudflare。

| ID | 需求與可驗收條件 |
|---|---|
| R-01 | Windows 可由 Setup 安裝，不要求安裝 Python；隨附 CLI 引導及部署文件。首次部署最終交付固定 endpoint、可用長效 KEY 及第三方串接訊息。 |
| R-02 | 每個裝置設定檔綁定一個自有 Cloudflare 帳戶及 Worker，使用 workers.dev 或安裝者既有網域。重啟、更新、同設定檔重複部署不變 URL、device_id、KEY。 |
| R-03 | CLI 訂閱與裝置身分分離；登入／登出／切換訂閱不自動輪替 KEY 或重建 Worker。DPAPI 綁定 Windows 使用者，跨 OS 帳戶需經授權恢復／配對。 |
| R-04 | 管理台可建立、輪替、撤銷 KEY。新 KEY 預設允許 Claude／Codex 全部已登錄模型，無每模型白名單；仍受來源 scope、模型目錄與訂閱限制。既有 KEY 不自動擴權，輪替保留 scope／RPM。 |
| R-05 | 標準同步 POST Chat Completions、GET models；長工作另有 jobs POST／GET。非串流為主要介面。非等價參數明確回 unsupported_parameter。 |
| R-06 | 每次呼叫可指定已登錄 model；省略或 auto 使用已保存預設，不用 MoE 自動挑選或付費 fallback。 |
| R-07 | usage 使用 CLI 回報 token，usage.cost 為該實際模型 OpenRouter 牌價 USD 等值。無有效牌價在推論前失敗；有用量但回應格式失敗仍保留可取得的計費 metadata。 |
| R-08 | 只持久化 allowlist metadata。管理台可篩選、CSV 匯出及清除已結束紀錄；不可保存 request／response 原文、附件、任意 metadata 或完整 KEY。 |
| R-09 | 推論不接續使用者個人 CLI session；使用獨立子程序／ephemeral 工作，不操作使用者視窗、不更動全域設定或登入。 |
| R-10 | Windows 管理台以系統 WebView2 顯示；保留預設瀏覽器備援。關閉管理視窗不停止背景服務，停止服務需明確操作。 |
| R-11 | 共用前端與 Windows 適配層分離。全頁沿用 AI GO 合約請款系統的深藍側欄／表頭、靛藍操作色、卡片／表單與深淺色語言，保留 Bridge 獨立產品名稱與功能。 |
| R-12 | 由 GitHub 專屬 Windows internal 渠道公告更新與最低版本；客戶端驗固定公鑰簽章、序號、來源及 SHA256，排空自有工作再套用。更新後 profile、KEY、URL、token／cost 不變。 |
| R-13 | 規格、資料、設計、決策、驗收及操作指引在 repo 與 Windows 包中可找到，不依賴任一 LLM 私有記憶。 |

## 非功能需求與邊界

- Windows 預設同時執行 1 筆，連同排隊最多 9 筆；每 KEY 預設 30 RPM，可設 1–600。Mac 並行設定由獨立維護者管理，這次不修改其行為。
- 管理 plane 只監聽 loopback 動態 port，驗 Host／Origin 與獨立管理憑證；client KEY 無管理權。固定外部 endpoint 與短效本機管理 URL 是不同概念。
- HTTPS Worker 與雲端 RAM 轉送可能離線／中斷；關機時網址仍存在，但不能承諾仍可推論。同步雲端等候有時限，未知執行結果不可自動重試以免重複計量。
- 淺／深色跟隨 OS；不載入外部字型、圖示 CDN、追蹤程式。窄版仍能導覽、操作；寬表在表格容器內水平捲動。
- 沒有公發 Authenticode 憑證；Ed25519 更新簽章不等於 Windows 安裝程式公發簽章。
- 不宣稱 OpenRouter 100% 相容、訂閱餘額查詢、通用 Responses API、串流、任意抽樣控制、模型路由或在本機執行呼叫端 tools。
- 不承諾 OS pagefile／crash dump 或供應商雲端零留存；保證範圍見 [架構](ARCHITECTURE.md) 的儲存邊界。

## 變更流程

新增需求附 R 編號與驗收案例。涉及資料、API、UI、身分或更新的變更同時更新相應文件；取捨加 D 編號。完成必須區分 source、CI、安裝包、已發布及正式已安裝，禁止以測試成功代替交付。
