# Local Token Buffet Bridge 改名驗收

## 已完成

- GitHub repo 改為 `local-token-buffet-bridge`；description 與 topics 採獨立產品定位，移除舊平台品牌。現行 repo 連結、安裝／Mac 交接 prompt 與發布操作已同步。
- 管理台標題、側欄、頁尾、Windows WebView 標題、Tk 備援與交接對話框改名。深藍／靛藍視覺由本專案獨立定義。舊租戶平台安裝與編號文件停用，歷史原文仍在 Git，不偽造替換網域的驗收證據。
- 本機回歸：334 passed、13 skipped；跳過項不冒稱通過。Node Relay 12、browser／Windows adapter 3。版本一致、文件覆蓋、秘密掃描及 22 個禁字檢查通過。
- headless Edge 真頁面：六頁 × 深淺色 × 1440／390px 共 24 組，標題與產品名稱、無舊品牌、側欄與整頁無橫向溢出，無 page error。使用合成隔離 preview，不讀正式 KEY、不操作使用者桌面。首輪發現共用 JS 會覆寫 HTML title，已修正並重跑通過。
- repo 改名後實際下載舊／新更新網址：policy bytes 相同、原 Ed25519 簽章有效、pack ID 與當前版本相同、簽署 feed SHA256 一致，共 6 項通過。原生正式版本當時為 0.9.0，policy sequence 8。這是連續性驗收，不代表新版已安裝。

## 保留與範圍

沿用原 profile／DPAPI／Keychain／pack ID／channel／執行檔相容名稱／自動啟動項。沒有重建裝置、endpoint、Worker 或 client KEY，也未修改供應商登入。技術 namespace 與 GitHub owner namespace 的處理見 [BRANDING](../BRANDING.md)。

改名 [PR27](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/27) 已合併，來源 `1de50fad55e66f0dcc8d85a5ad930e1d10db01c6`、共用版本 0.9.2；全部 checks 通過，Windows native 54／54、拋棄 runner 電源 8／8。[publish 39906228365](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39906228365) 成功，Windows 0.9.1 已公開。匿名下載、asset size／hash、包內品牌／文件／runtime、舊客戶端更新發現及原簽章共 22 項通過；policy sequence 9、minimum 0.7.0、公鑰 fingerprint `9682eb28e5ab9020`。

使用者追加 issue #20 後，正式 Windows 暫留 0.9.0，等待整合 Windows 0.9.2 後一次受控更新；不能把公開 0.9.1 說成正式機已安裝。後續結果見 [全機單實例收據](2026-10-23-windows-machine-runtime.md)。未發布或操作 Mac 服務，未部署安裝者 Cloudflare。
