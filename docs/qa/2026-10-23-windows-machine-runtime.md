# Windows 0.9.2 全機單實例驗收

對應 issue #20、R-21、A-11、D-30。只修改 Windows 啟動、控制、建包與測試整合；Mac 行為不變，不發布 Mac 或部署安裝者 Cloudflare。

## 候選來源已驗

- 真 Winsock 獨占 reservation，不 listen、不繼承 handle；重綁與連線負面測試、釋放後再取得。
- 合成 profile 在拒啟動前後 SQLite bytes 相同；Store 不被開啟。六個程序同時競爭恰一個成功。
- source 真程序的同 profile 重開、其他 profile 拒絕、正常關閉／強制終止後再啟動；Runtime／API／relay 初始化故障釋放資源。
- 初步 guard＋console boundary 26 項通過。完整回歸、frozen Setup→A→B、真跨標準使用者／TS session、公開 release 與正式更新仍需各自收據；不因原子機制正確就冒稱實機跨 session 已驗。

本機完整回歸 345 passed／13 skipped，Relay 12／adapter 3，文件覆蓋、品牌、secret 與 22 個禁字檢查通過。跨使用者 harness 已完成語法檢查，但沒有在 owner 工作站執行，結果以 disposable CI 收據為準。

首輪 [Windows CI 39908044074](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39908044074) 的獨立 machine-ownership job **12／12 通過**：實際 parent TS session 2、標準使用者 session 0，雙向互斥、DPAPI 拒絕、釋放後標準帳戶可啟動 HTTP、正常停止可再接手，測試 task／帳號移除。最後來源仍須全部 checks 通過，不能把首輪單 job 當成整包驗收。

同 profile 的 source 喚回測試會捕捉 browser callback 並確認實際 activation event 已處理，不開 owner 桌面瀏覽器；Windows native WebView 複製／匯出／關窗另在 runner 驗證。

## CI 與正式閘門

CI 的 `tools/verify_windows_machine.py parent` 只允許 Actions Windows disposable runner，建立一個暫時標準帳號與 SYSTEM broker，密碼只在 parent RAM，以 duplicated token handle 啟動另一真實 TS session 的非互動子程序。檢查非管理員、不同 SID／TS session、拒絕前不建 profile、DPAPI 管理憑證不可跨使用者解密、原 owner 釋放後可啟動、反向拒絕、正常退出可接手，最後刪除帳號與 task。這不是產品安裝步驟，不在 owner 工作站執行。

正式驗收沿用原 URL、KEY、DPAPI、資料、onboarding 與牌價計算；只排空及重啟 Bridge，不重開電腦、不操作其他 CLI 視窗。舊 Windows 0.9.0／0.9.1 不持有新鎖，升級時須先正常停止；不能聲稱新鎖會讓任意舊 binary 自動遵守。
