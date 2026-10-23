# Mac 0.9.1-mac.1 發布驗收

範圍：R-21／R-22、A-11／A-12、D-27／D-28；Mac 全機單實例、現行 BYO source Release、雙平台 README／Agent 引導、公開下載安裝與 owner 更新。Windows 原生修復由 issue #20 另行負責，不改 Windows release-target／policy 或使用者 Worker。

## 修正來源

原 PR #21 的 Mac CI 在子程序 readiness 的 kqueue wait 15 秒逾時；本輪改用直接 pipe reader、有限冷啟動預算及錯誤清理，保留真程序／HTTP 驗證，沒有略過測試。原基底分支因 #17 合併刪除而關閉 #21，本輪直接以 main 開完成 PR。整合 Windows 0.8.2 後保留其 D-25；Mac 單實例決策為 D-26。

歷史 Mac builder 只裝 desktop/ 舊產品線；本輪新增 tracked 公開檔 allowlist 的現行 BYO source ZIP，包含 Python 3.12+ Install.command、當前 desktop_bridge／Worker 範本／完整產品與 Agent 文件，不含任何 profile 或憑證。原始碼 release metadata 保留無 .git 下載安裝的來源 commit。Mac 正式交付格式是 source ZIP；未宣稱公證 .app／DMG 或 Windows 更新機制。

## 驗證收據

本機回歸、原生 renderer、Mac CI、合併、Release 公開下載、下載包安裝及 owner 真升級／HTTPS 的實際結果，隨執行完成追加於本節。測試只用合成內容與可撤銷測試 KEY；完整 KEY／原始 I/O 不落盤，owner KEY rows 與原設定比較後保留。

- 本機 `pytest desktop_bridge/tests packaging/windows/tests tools/tests desktop_platform/macos/tests -q`：264 passed／5 skipped；新 package 測試驗 allowlist、現行來源、checksum／commit／可執行入口，以及 dirty 包不能宣布。
- 真 Cocoa `tools/verify_macos_console.py`：48 個 light／dark × 1200／480px 版面變體，六頁與五步精靈無全頁橫向溢出；真剪貼簿讀回後還原、CSV 真 NSSavePanel Cancel／自動選中文檔名 Save、導覽界線、KEY 清空、關 viewer 後 HTTP 仍 200 全通過。
- Node relay 8、Windows platform 2；產品文件、版本一致、secret scan、diff check 全通過。private terms 由 repo-secret CI 放行，不偽造本機清單。

- clean commit `5649afa` 的現行 ZIP 已在本機從解壓的 Install.command 真安裝到獨立目錄；安裝 manifest 保留原 Release SHA，真 HTTP 新版、固定全機鎖、第二 profile 無 DB、正常停止後 API 關閉全通過。
- 原生畫面檢視找出 Mac 更新卡仍稱沒有公開包，已改為 Release source ZIP／手動下載說明；重跑完整 48 畫面及原生操作全通過。

- 發布前主線新增已合併 #23（core 0.9.0、模型目錄／Decisions）；完整保留新功能與 Windows 安全碼後重整合。Mac 最終版改為 0.9.1-mac.1，R-21／R-22、D-27／D-28 避免覆蓋先合併的 ID，重新跑 Mac／共用／原生驗收。

- 整合 0.9.0 後重跑：332 passed／13 個 Windows／PowerShell 平台案例 skipped；Node relay 12、platform 3 passed。新版 48 畫面／原生操作與現行 ZIP 安裝再次全通過。另補啟動中途失敗的完整清理：API 已開但 relay 建立失敗時先關 HTTP／停止 runtime，再釋放全機鎖；新增第 10 個單實例案例通過。
