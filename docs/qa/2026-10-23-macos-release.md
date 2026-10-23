# Mac 0.9.1-mac.1 發布驗收

狀態：**merged／published／download-installed／owner-installed-verified 全部完成**。

範圍：R-21／R-22、A-11／A-12、D-27／D-28；Mac 全機單實例、現行 BYO source Release、雙平台 README／Agent 引導、公開下載安裝與 owner 更新。Windows 原生修復由 issue #20 另行負責，不改 Windows release-target／policy 或使用者 Worker。

## 修正來源

原 PR #21 的 Mac CI 在子程序 readiness 的 kqueue wait 15 秒逾時；本輪改用直接 pipe reader、有限冷啟動預算及錯誤清理，保留真程序／HTTP 驗證，沒有略過測試。原基底分支因 #17 合併刪除而關閉 #21，本輪直接以 main 開完成 PR。整合 Windows 0.8.2 後保留其 D-25；Mac 單實例決策為 D-26。

歷史 Mac builder 只裝 desktop/ 舊產品線；本輪新增 tracked 公開檔 allowlist 的現行 BYO source ZIP，包含 Python 3.12+ Install.command、當前 desktop_bridge／Worker 範本／完整產品與 Agent 文件，不含任何 profile 或憑證。原始碼 release metadata 保留無 .git 下載安裝的來源 commit。Mac 正式交付格式是 source ZIP；未宣稱公證 .app／DMG 或 Windows 更新機制。

## 驗證收據

本機回歸、原生 renderer、Mac CI、合併、Release 公開下載、下載包安裝及 owner 真升級／HTTPS 已完成，實際結果如下。測試只用合成內容與可撤銷測試 KEY；完整 KEY／原始 I/O 不落盤，owner KEY rows 與原設定比較後保留。

- 本機 `pytest desktop_bridge/tests packaging/windows/tests tools/tests desktop_platform/macos/tests -q`：264 passed／5 skipped；新 package 測試驗 allowlist、現行來源、checksum／commit／可執行入口，以及 dirty 包不能宣布。
- 真 Cocoa `tools/verify_macos_console.py`：48 個 light／dark × 1200／480px 版面變體，六頁與五步精靈無全頁橫向溢出；真剪貼簿讀回後還原、CSV 真 NSSavePanel Cancel／自動選中文檔名 Save、導覽界線、KEY 清空、關 viewer 後 HTTP 仍 200 全通過。
- Node relay 8、Windows platform 2；產品文件、版本一致、secret scan、diff check 全通過。private terms 由 repo-secret CI 放行，不偽造本機清單。

- clean commit `5649afa` 的現行 ZIP 已在本機從解壓的 Install.command 真安裝到獨立目錄；安裝 manifest 保留原 Release SHA，真 HTTP 新版、固定全機鎖、第二 profile 無 DB、正常停止後 API 關閉全通過。
- 原生畫面檢視找出 Mac 更新卡仍稱沒有公開包，已改為 Release source ZIP／手動下載說明；重跑完整 48 畫面及原生操作全通過。

- 發布前主線新增已合併 #23（core 0.9.0、模型目錄／Decisions）；完整保留新功能與 Windows 安全碼後重整合。Mac 最終版改為 0.9.1-mac.1，R-21／R-22、D-27／D-28 避免覆蓋先合併的 ID，重新跑 Mac／共用／原生驗收。

- 整合 0.9.0 後重跑：332 passed／13 個 Windows／PowerShell 平台案例 skipped；Node relay 12、platform 3 passed。新版 48 畫面／原生操作與現行 ZIP 安裝再次全通過。另補啟動中途失敗的完整清理：API 已開但 relay 建立失敗時先關 HTTP／停止 runtime，再釋放全機鎖；新增第 10 個單實例案例通過。

- 最終啟動清理版全量回歸 333 passed／13 個平台跳過；CLAUDE／CONTRIBUTING 與 BYO skill 一併改為現行雙平台入口、Mac source 發布及正常更新不重部署，避免包內仍帶歷史維護步驟。

## 最終合併、發布與已安裝收據

- [完成 PR #24](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/24) 的 14 項 checks 全成功後 squash merge。main／Release runtime source：`e3c09bb7cb478220413f5e2c75dc35183e689675`，Mac `0.9.1-mac.1`；保留已合併 0.9.0 功能與 Windows 安全修補，沒有發布 Windows 或部署 Worker。
- [Mac 發布 run 39903843916](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39903843916) 成功：main 的 Mac source tests、真 Cocoa renderer、現行 ZIP 建包／安裝／固定鎖／停止，以及歷史回歸均放行，再核對 clean SHA／版本／hash 發布。
- 已公開 [Mac source Release](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.1-mac.1)。4 個附件皆匿名下載成功：ZIP、其 SHA256、macos-source-manifest.json、macos-source-self-test.json。ZIP 1,514,265 bytes；SHA256 `96776675d280b00d7a1c52829632bf47ea591c993e799060ac023acb2cc1f197`；manifest 來源為上述 main SHA，dirty=false／redistributable=true。
- 從實際公開下載的 ZIP，再經 Install.command 在隔離目錄真安裝：安裝來源 SHA／版本吻合，HTTP 健康、固定全機鎖拒絕第二 profile 且未建立 DB、正常停止後 API 無法連線，全通過。這是下載包的實測，非僅對本機建包宣稱公開附件可用。
- owner Mac 由 `0.8.1-mac.1`／`936ff38` 更新為 `0.9.1-mac.1`／`e3c09bb`，來源為匿名下載並驗 hash 的公開 ZIP。經原安裝工具 pause／wait-idle／停止／同 data-dir 安裝／重啟，並保存解壓來源供日後明確更新。沒有重新登入、重建 Worker、輪替 owner KEY 或改電源／鎖定。
- 同一臨時 Codex KEY 在更新前後外部 models GET 200。device ID、固定 URL、Cloudflare 帳戶／Worker、全部 owner KEY rows、已登錄模型／預設、relay 設定與四路容量一致；新增模型目錄可回傳額外發現項目，不把動態目錄數量當成資料遺失。
- 更新後真外部 HTTPS Chat 200／5.076 秒，`usage.cost=0.008450` USD，實際 model `openai/gpt-6.1-sol`；只讀取到請求前後皆鎖定，未改鎖定狀態。相同 UUID 去重、JSON schema 200、工具提案 200／未代執行工具、temperature 400 unsupported_parameter、handoff 欄位完整均通過。臨時 KEY 撤銷，原 1 把有效 owner KEY 完整保留。
- 發布前另以合成隔離資料真跑本機 Codex：Chat PONG 通過／5.666 秒／cost 0.0026152；Decisions noul 通過／6.106 秒／cost 0.009122。這是本機 0.9 整合證據；既有 Worker 未部署新路徑，依 JEV-COMPATIBILITY 的安裝者部署界線處理，不將本機結果冒稱外部 Decisions 已部署。
- 最後逐檔核對已安裝 51 個 Python／JS／CSS／HTML 與公開 source ZIP 相同；原 profile 背景重開成功、不新增 runtime；另一全新 profile＋API port 0 被拒且無 SQLite。最終 HTTP 為新版、ok=true、accepting=true，四路容量及 1 把 owner KEY 保留。

## 完成範圍與固定契約

Mac 的本次修復、原生驗證、Release、公開下載安裝、owner 真升級與外部標準呼叫已交付，沒有待處理的 Mac 發布／修復項。source ZIP 是支援的發布格式；Python 3.12+、登入後 LaunchAgent、清醒與連網、CLI／Keychain 可用都是操作條件。公證 .app／DMG、Windows policy、自動跨使用者憑證搬移與供應商模型業務校準不屬於本次格式／能力。

既有 onboarding／電源同意紀錄原樣保留；這是已部署裝置的更新驗收，未代本人勾選、偽造首次設定完成或重做帳戶 OAuth。關 viewer X 繼續背景供應；真正停止使用管理台「結束 Bridge」，或 mac_service.py stop 先排空。Windows 全機 runtime 修復仍由 issue #20 的 Windows session 管理，不列為 Mac 發布未完成。

- 收據提交期間 repo 改名為 `AI-GO-APP/local-token-buffet-bridge`；核對 repository ID 1390643409 相同，沿用原 PR／tag／assets。新 canonical URL 再次匿名下載 ZIP，SHA256 完全相同。CI 的必填 terminology 判斷改用固定 repository ID，避免改名影響原 gate；不改 Release runtime／附件。
