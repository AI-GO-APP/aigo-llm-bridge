# Mac 0.9.4-mac.1 併發交付

整合已合併 [PR #32](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/32)，來源 main 8310be60d0feab60f70cd9513695d7f8a0d646b9。Mac source 新 profile 預設共享 64；既有 profile 先保留容量，owner 本次授權更新後明確設為 64。Mac 一次性交付 Key 的預設改為 600 RPM，既有 Key 不改寫。

本輪依 owner 要求只完成基本安裝、同一 Worker 部署及少量合成 Chat／Decisions HTTPS 與成本收據驗證，後續新增授權本機 Claude 64 併發測試；結果待實測記錄。自動化隔離測試不代表訂閱負載實測。保留原 profile、URL、owner Key、Cloudflare 帳戶及 CLI 登入，不改電源或鎖定。

目前為候選紀錄；合併、CI、發布、公開下載及正式安裝證據將於實際完成後補記。

本機 Python Bridge／tools 回歸 281 passed、18 skipped；Worker 13 passed，文件、品牌、版本與 diff 檢查通過。本機沒有私有 terms 清單，`lint_terms.py --require` 未通過，必須由 repo-secret CI 核實。Claude 官方 auth login 已由本人完成，後續切換預設為 Haiku 4.5，保留 Codex 明確模型路由及原 Key scope。

Mac Claude 登入適配：官方登入成功後，完整本機環境 auth status=true，但原 allowlist 環境=false。逐欄比對僅補回 USER 即恢復 claude.ai／Max 認證；保留此非敏感使用者名稱，不外傳憑證，API key 等無關 secret 仍排除。新增回歸覆蓋。

## 0.9.5-mac.1：LaunchAgent 檔案描述符上限

在 0.9.4-mac.1 之上補 macOS 專屬的檔案描述符限制。

### 問題

LaunchAgent 啟動的 Bridge 繼承 `launchctl limit maxfiles` 軟上限 256。在 256 上限下以 64 個真實子程序（每個 stdin／stdout／stderr pipe）經本機 HTTP 並行呼叫，只有 39–41 筆執行完成，其餘回 500。Windows 沒有此限制，因此 Windows 驗收不能代表 Mac 通過。

### 修正

POSIX 啟動 `serve()` 前將本程序 RLIMIT_NOFILE 軟上限提高到 4096（不超過硬上限）。不修改 launchctl、sysctl 或其他程序。

### 候選原始碼驗證（macOS，Python 3.12）

- 新增回歸：含新增「256 上限下 64 個真實子程序 HTTP 全數 200」測試，移除修正時該測試只有 39／64 成功。
- Worker relay 13 passed；tools 56 passed；品牌與產品文件檢查通過。禁字清單檔不在本機，`lint_terms --require` 由 CI 執行。
