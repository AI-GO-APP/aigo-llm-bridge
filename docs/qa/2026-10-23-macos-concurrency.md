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

### 已安裝版本實機驗收（2026-10-23）

- 原設定檔以 `mac_service.py update` 更新為 0.9.5-mac.1；profile、URL、owner Key 保留，`inference_workers=64`，本機 `/health` 回 `max_concurrent_requests:64`、`shared_provider_capacity:true`。Claude／Codex 訂閱狀態皆 ready。
- Claude 真實訂閱低用量壓測（`anthropic/claude-haiku-4.5`、提示「Reply exactly OK.」、無工具／串流，臨時 claude scope Key 測後撤銷）：

| 同時 | 成功 | 內容正確 | 牆鐘 | p50／p95／max | input／output tokens | usage.cost | Bridge fd 峰值 | CLI 子程序峰值 |
|---|---|---|---|---|---|---|---|---|
| 1 | 1／1 | 1 | 2.1 s | 2.1／2.1／2.1 s | 563／82 | 0.0010 | 56 | 1 |
| 16 | 16／16 | 16 | 3.5 s | 2.8／3.5／3.5 s | 9,005／1,066 | 0.0143 | 101 | 16 |
| 64 | 64／64 | 64 | 10.0 s | 8.4／9.2／10.0 s | 36,029／4,210 | 0.0571 | 261 | 64 |

- Chat／Decisions 混合 64（各 32，Haiku 4.5，每筆唯一 `X-AIEA-Request-Id`）：64／64 通過，回應模型、答案格式與 `usage.cost` 皆有效，64 筆 UUID 收據 `billing_status` 完整且成本與回應一致；Bridge 同時執行峰值 58，總時間 54.0 s（p50 11.8 s，Decisions 最慢 54.0 s），usage.cost 合計 0.3043。臨時 Key 測後撤銷。
- 64 筆占滿時加送的第 65 筆在推論前回 429 `queue_full`，不消耗訂閱。64 段 fd 峰值 261 已超過 LaunchAgent 原 256 上限，證實本修正為必要條件。
- 公開 Worker：以 `byo_setup.py deploy` 原地更新同一名稱／URL（0.9.4-relay 範本，64 推論＋8 控制名額），未重寫配對 secret。部署前後所有公開路徑皆回 Cloudflare 1101；`wrangler tail` 例外為 Durable Objects 免費方案每日執行時間配額已用盡，非程式錯誤。Relay 長輪詢使 DO 幾乎全天保持活躍，免費配額餘裕很小；公開 HTTPS 64 併發待配額重置（UTC 00:00）或改用付費方案後驗證。
- 本機 Node 22.14.0 低於部署基線，部署改用 nodejs.org 官方 v22.23.4（SHA256 驗證）置於使用者目錄，未改系統 Node。
