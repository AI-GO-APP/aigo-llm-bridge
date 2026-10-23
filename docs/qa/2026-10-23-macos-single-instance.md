# Mac 全機單實例修復驗收（2026-10-23）

Mac source `0.8.1-mac.2`；對應 R-19／A-11／D-25。PR 以既有 Mac parity 分支為基底；未合併、未發布、未升級 owner 已安裝 Bridge，未部署 Worker。Windows 由 [issue #20](https://github.com/AI-GO-APP/aigo-llm-bridge/issues/20) 另修與驗收。

## 實作範圍

- 全機固定 loopback TCP 8919 的獨占 bind，不 listen、不交換資料、不持久化 secret；不隨 profile／使用者／API port 改變。
- 相同 profile 仍用原 instance lock／activation 喚回管理視窗；不同 profile 在 Store／Runtime／API／relay 前拒絕，foreground exit 2；background busy exit 0 避免 LaunchAgent 失敗重啟迴圈。
- OS 於正常退出或 kill 後釋放資源，無 stale PID 檔判定，fd 不傳給 CLI 子程序。保留原 profile／Worker／URL／KEY。
- 管理視窗 X 保留背景供應；明確結束會取消未完成工作；Mac service stop 先 pause／wait-idle 再 bootout，disable 另移除登入自啟。此次未改關窗契約或 UI。

## 本輪證據

- `python -m pytest desktop_bridge/tests -q`：137 passed，2 skipped，包含新增 9 個單實例案例。真 subprocess 驗不同 profile／不同 API port 的拒絕、原服務仍健康、正常 SIGTERM 與 SIGKILL 後重啟、停止後 HTTP port 無法連線；6 個程序同時競爭恰一個取得所有權。回讀既有 DB 證明被拒啟動不將 running 標成 interrupted；初始化與 API bind 失敗可釋鎖。
- 本機 macOS 真入口煙霧：使用臨時合成 profile、原版 `sys.platform`、正式固定鎖地址 8919；第一套 `/health` 正常，第二 profile＋API port 0 被拒且未建立 SQLite。第一套 SIGTERM 後原 API 無法連線，第二 profile 隨後成功啟動並正常停止。未使用 CLI 訂閱、KEY、Keychain 或外部 relay。
- `node --test cloudflare/test/relay.test.js`：8 passed；Windows frontend platform：2 passed。
- 合併範圍回歸 `python -m pytest desktop_bridge/tests packaging/windows/tests tools/tests -q`：259 passed，4 skipped。原 Mac runtime 缺少 Windows signing 的 cryptography，首次收集失敗；依 repo signing hash lock 將相依套件安裝至臨時測試目錄後重跑通過，未修改 owner 已安裝 runtime。
- `tools/check_product_docs.py`、`tools/version.py --check`、`tools/scan_secrets.py`、`git diff --check` 通過。Mac source 版本與四常數／client 副本一致，Windows package target 不變。CI 尚待 PR 觸發，不以本機結果替代。

## 證據限制

- 跨 macOS 使用者的互斥依 OS 全機 TCP bind 語意實作，這次沒有登入第二個實際 OS 帳號驗收；不能稱已完成真跨使用者實機測試。
- 單元／程序案例使用隔離鎖地址避免干擾 owner 服務，正式入口煙霧另外驗固定 8919；產品沒有變更鎖地址的 CLI／env 選項。
- 舊版不持有此鎖，升級前須正常停止舊 runtime；不能保證任意歷史 binary 或自行改碼仍遵守限制。既有 owner 舊版保持原狀，未將隔離新候選測試當成已完成 owner 升級。
- 未重新做 UI 視覺、真訂閱推論、公開 HTTPS、跨使用者、LaunchAgent 登入自動啟動／真更新或 Windows native 驗收；Windows 全機鎖仍未實作。本輪不更動電源、鎖定、CLI 登入或外部帳戶。
- 本機沒有 private terminology 清單，`python tools/lint_terms.py --require` 明確失敗；不建立替代清單，交由有 repository secret 的 CI 執行。
