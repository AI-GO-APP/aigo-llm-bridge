# Local Token Buffet Bridge 改名驗收

## 已完成

- GitHub repo 改為 `local-token-buffet-bridge`；description 與 topics 採獨立產品定位，移除舊平台品牌。現行 repo 連結、安裝／Mac 交接 prompt 與發布操作已同步。
- 管理台標題、側欄、頁尾、Windows WebView 標題、Tk 備援與交接對話框改名。深藍／靛藍視覺由本專案獨立定義。舊租戶平台安裝與編號文件停用，歷史原文仍在 Git，不偽造替換網域的驗收證據。
- 本機回歸：334 passed、13 skipped；跳過項不冒稱通過。Node Relay 12、browser／Windows adapter 3。版本一致、文件覆蓋、秘密掃描及 22 個禁字檢查通過。
- headless Edge 真頁面：六頁 × 深淺色 × 1440／390px 共 24 組，標題與產品名稱、無舊品牌、側欄與整頁無橫向溢出，無 page error。使用合成隔離 preview，不讀正式 KEY、不操作使用者桌面。首輪發現共用 JS 會覆寫 HTML title，已修正並重跑通過。
- repo 改名後實際下載舊／新更新網址：policy bytes 相同、原 Ed25519 簽章有效、pack ID 與當前版本相同、簽署 feed SHA256 一致，共 6 項通過。原生正式版本當時為 0.9.0，policy sequence 8。這是連續性驗收，不代表新版已安裝。

## 保留與範圍

沿用原 profile／DPAPI／Keychain／pack ID／channel／執行檔相容名稱／自動啟動項。沒有重建裝置、endpoint、Worker 或 client KEY，也未修改供應商登入。技術 namespace 與 GitHub owner namespace 的處理見 [BRANDING](../BRANDING.md)。

此修改的 Windows 安裝目標為 0.9.1、共用來源版本為 0.9.2。Windows native CI、公開發行及正式更新收據在完成後補充；此文件目前不宣稱它們已通過。不發布或操作 Mac 服務，不部署安裝者 Cloudflare。
