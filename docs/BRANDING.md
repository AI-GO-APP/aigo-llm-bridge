# Local Token Buffet Bridge 產品識別與改名

產品名稱為 **Local Token Buffet Bridge**，repository 名稱為 `local-token-buffet-bridge`。這是獨立的本機訂閱轉接產品；安裝、授權、BYO Cloudflare、API、安全與發布規格均由本 repo 維護，不需要外部租戶平台。

## 改名範圍

管理台標題、側欄、頁尾、Windows 視窗、原生備援視窗、交接對話框、README、設計規範、安裝／維護／發布文件及 GitHub 專案描述統一採新識別。過時的平台部署指令停用，歷史原文留在 Git 版本紀錄，不再當作安裝指南。

GitHub 組織是存放 repository 的帳戶 namespace，不是產品名稱或執行依賴。本次改 repo 名稱，沒有搬移組織、購買網域或變更任何安裝者 Cloudflare 專案。

## 舊安裝相容性

產品改名不遷移或重建任何使用中的資料。既有設定檔、DPAPI／Keychain 服務識別、安裝 pack ID、可執行檔相容名稱、自動啟動登錄、更新公鑰與 channel 維持相同。文件中程式碼區段保留必要的既有技術識別，避免使用者依文件操作時找不到原安裝。它們不是產品品牌，也不代表外部平台整合。

裝置 ID、Worker 名稱、固定 endpoint、長效 client KEY、訂閱登入、SQLite metadata 與計價契約均不因改名而改變。不得為消除舊路徑字串而複製設定檔、重建 Worker、重新授權或輪替 KEY。

新來源使用新 repo 連結。舊安裝內已簽署的更新設定及歷史 release 資產不覆寫；驗收須實際從舊網址下載，核對轉址後的簽章、目標、序號及資產 hash，再由原更新機制處理新版。

## 維護檢查

執行 `python tools/lint_branding.py`。CI 檢查所有 tracked Markdown、LICENSE 與共用前端，禁止重新加入已撤下的產品歸屬、平台安裝網址與舊 repo 連結。GitHub owner namespace 與相容性技術識別保留；不改寫 Git 歷史，也不把既有 immutable release 宣稱為已重製的新品牌包。
