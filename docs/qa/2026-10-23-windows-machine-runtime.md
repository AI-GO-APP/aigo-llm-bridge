# Windows 0.9.2 全機單實例驗收

**完成狀態：merged／published／owner-installed／restart-verified。** [PR28](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/28) 已合併並關閉 issue #20；Windows 發行來源 `11d596ee4e162aad749e1583e0efa3a11da78b22`，正式 Windows 從 0.9.0 直接升到 0.9.2。以下候選／首輪紀錄保留歷史，最後結果以本節及文末完成收據為準。

對應 issue #20、R-21、A-11、D-30。只修改 Windows 啟動、控制、建包與測試整合；Mac 行為不變，不發布 Mac 或部署安裝者 Cloudflare。

## 候選來源已驗

- 真 Winsock 獨占 reservation，不 listen、不繼承 handle；重綁與連線負面測試、釋放後再取得。
- 合成 profile 在拒啟動前後 SQLite bytes 相同；Store 不被開啟。六個程序同時競爭恰一個成功。
- source 真程序的同 profile 重開、其他 profile 拒絕、正常關閉／強制終止後再啟動；Runtime／API／relay 初始化故障釋放資源。
- 初步 guard＋console boundary 26 項通過。完整回歸、frozen Setup→A→B、真跨標準使用者／TS session、公開 release 與正式更新仍需各自收據；不因原子機制正確就冒稱實機跨 session 已驗。

本機完整回歸 345 passed／13 skipped，Relay 12／adapter 3，文件覆蓋、品牌、secret 與 22 個禁字檢查通過。跨使用者 harness 已完成語法檢查，但沒有在 owner 工作站執行，結果以 disposable CI 收據為準。

首輪 [Windows CI 39908044074](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39908044074) 的獨立 machine-ownership job **12／12 通過**：實際 parent TS session 2、標準使用者 session 0，雙向互斥、DPAPI 拒絕、釋放後標準帳戶可啟動 HTTP、正常停止可再接手，測試 task／帳號移除。最後來源仍須全部 checks 通過，不能把首輪單 job 當成整包驗收。

同 profile 的 source 喚回測試會捕捉 browser callback 並確認實際 activation event 已處理，不開 owner 桌面瀏覽器；Windows native WebView 複製／匯出／關窗另在 runner 驗證。

新增 activation fixture 首輪把第二次啟動也帶 background，按契約不通知視窗，因此兩個案例等候逾時；已改成真正的前景重開，並保留原失敗紀錄。這不是放寬等待條件或變更背景啟動語意。

## CI 與正式閘門

CI 的 `tools/verify_windows_machine.py parent` 只允許 Actions Windows disposable runner，建立一個暫時標準帳號與 SYSTEM broker，密碼只在 parent RAM，以 duplicated token handle 啟動另一真實 TS session 的非互動子程序。檢查非管理員、不同 SID／TS session、拒絕前不建 profile、DPAPI 管理憑證不可跨使用者解密、原 owner 釋放後可啟動、反向拒絕、正常退出可接手，最後刪除帳號與 task。這不是產品安裝步驟，不在 owner 工作站執行。

正式驗收沿用原 URL、KEY、DPAPI、資料、onboarding 與牌價計算；只排空及重啟 Bridge，不重開電腦、不操作其他 CLI 視窗。舊 Windows 0.9.0／0.9.1 不持有新鎖，升級時須先正常停止；不能聲稱新鎖會讓任意舊 binary 自動遵守。

## 最終 CI、公開下載與已安裝收據

- 最後來源 `078d7c5` 的所有 PR checks 通過；[Windows native 39908602015](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39908602015) 的 Setup→A→B／WebView／native＋source 拒啟動 **58／58**、真標準使用者／TS session **12／12**、拋棄 runner 電源 **8／8**。同 profile 前景重開會處理喚回 event，background 重開不強迫開窗；拒啟動不修改既有 sentinel DB。
- [Windows publish 39909255846](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39909255846) 成功並重跑原生與跨使用者閘門。[0.9.2 internal Release](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/windows-installer-internal-v0.9.2) 已公開，沒有 Authenticode 公發憑證；Mac／Cloud 未部署。
- 匿名 HTTPS 下載全數 assets，size／SHA256、包內來源／品牌／文件／CA／runtime、舊安裝更新發現及原公鑰簽章 **22／22**。Policy sequence **10**、minimum **0.7.0**、expires **2026-11-22T06:10:25.397134+00:00**、signer fingerprint **9682eb28e5ab9020**；最低版本未提高，不把此次更新說成所有使用者被強制升級。
- 正式從 0.9.0 走原更新器排空／備份／升級／重啟，安裝版與來源吻合。原 **7 筆設定、35 筆 KEY 紀錄、203 筆既有終態 request metadata** 的內容 hash 全保留，公開 URL／device identity、裝置配對 DPAPI、onboarding 不變。新 metadata 依正常呼叫新增，原兩支有效 caller KEY 保留。
- 正式機拒絕第二個 source、native controller 與 native background runtime；同 profile background 重開正常退出；拒方 DB bytes 完全相同，原服務仍接單，共 **8／8**。8919 只有 reservation、沒有 listener。
- 明確 drain／shutdown 後，核對原 service 程序退出、本機 API 關閉、全機鎖釋放、沒有殘留自有子程序；帶有效 KEY 的公開推論 POST 回 **408**，沒有本機 request 執行。等待該請求到期清除後，沿原 profile 重啟並恢復原接單狀態，共 **8／8**。沒有用短暫的 Worker health.online 當作推論證據。
- 升級後與受控重啟後各一次真實 Codex `openai/gpt-6-luna` HTTPS chat：每次 input **8563**、output **6**、`usage.cost` **0.0008593 USD**；與公開牌價及 receipt 的計算一致，billing complete。這是訂閱用量的 API 牌價估值，不是額外 API 扣款。
- 合成內容標記與完整驗收 KEY 未出現在 profile；原文仍只在 RAM。臨時 KEY 最後撤銷，外部 GET 回 401，保護檔已刪除，原兩支有效 KEY 保留。最後 **9／9** 核對 actual runtime、已安裝 EXE 與公開包 hash、來源、接單、API／machine reservation 同一 PID 及兩支原 KEY。PID 核對採 LISTEN 狀態，排除 TIME_WAIT／PID 0，原始測試收據不覆寫成成功。

| 公開資產 | SHA256 |
|---|---|
| full nupkg，33870374 bytes | `601ac638c317f156c8206336d080b5bac7138122da12c0890e194d3129859f0a` |
| Setup.exe，41384486 bytes | `9a1848f42a4bcbabac4dfc473ffd42427a5ecb577552835e1748e0e8361e5146` |

私有收據位於維護者的 ignored `.desktop-build/`：`machine-native-final/`、`machine-ci-final/`、`machine-publish-proof/`、`windows092-release-readback/`、`machine-production-rejection/`、`rename-production/`。不提交安裝者設定、完整 KEY、DPAPI blobs、原始 I/O 或工作站路徑。本輪未執行 OS reboot、真跨 owner 帳號登入、Mac 發布或 Cloud 變更；跨 OS 使用者／TS session 的實測在 disposable runner 完成。
