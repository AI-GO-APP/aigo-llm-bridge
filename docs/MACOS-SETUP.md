# Mac 設定、常駐與來源更新

Mac source 候選 `0.8.0-mac.1` 同步 Windows 0.7.3 設計及 0.8.0 首次設定流程，使用 Cocoa／WKWebView、登入 Keychain 與使用者 LaunchAgent。實測範圍見 [Mac 同步 QA](qa/2026-10-23-macos-parity.md)。不發布 Mac release／DMG，Windows 發布渠道不適用 Mac。

## 安裝與管理視窗

依 [source 安裝](CROSS-PLATFORM-INSTALL.md) 執行 `python3 tools/install.py`。安裝器在專用 runtime 安裝鎖定版 pywebview 及 Cocoa 依賴，隨附產品文件。`Bridge.command` 開啟原生管理視窗，原生環境不可用時回退預設瀏覽器。關閉視窗不停止背景 Bridge；再次使用捷徑可開回原視窗。完整停止使用管理台「結束 Bridge」或 `mac_service.py stop`。

六頁設計、深淺色、窄版、模型映射、KEY 生命週期、metadata 篩選及 CSV 與 Windows 共用。Mac 適配提供系統剪貼簿及 Save／Cancel；瀏覽器保留 Clipboard／下載備援。原生操作只接受綁定的 loopback 管理頁。管理 token 經子程序 stdin 傳遞，不寫控制檔或 argv。

## 五步首次設定

1. 檢查插電自動睡眠，明確同意後套用。已是 `sleep 0` 只讀回；需要變更時本人點選系統管理員授權。保留電池、顯示器、螢幕保護、鎖定、闔蓋及實體按鍵行為。
2. 檢查 Codex／Claude 訂閱，已就緒則沿用。只有本人按登入才開新的 Terminal 執行官方登入，不操作既有 CLI 視窗。CLI 安裝及瀏覽器 OAuth 由本人處理；Bridge 尚有工作時拒絕發起來源登入。
3. 準備 Node.js 22+／Wrangler 4.95.0，完成自己的 Cloudflare OAuth，明確選定自有帳戶。部署登入、LLM 訂閱、Keychain 裝置 secret 與 client KEY 分離。
4. 選一鍵部署或複製此安裝位置專用的 AI IDE prompt。沿用同一帳戶、裝置與 Worker 的 plan／verify／publish 流程。開啟管理台不代表部署授權，不能直接部署 repo 範本。
5. 建立或貼回已保存的長效 KEY，選模型並明確按一次真 HTTPS 測試。GET models 成功後只發一次合成 POST，需取得 PONG 與有限、非負數值的 `usage.cost`。保存 KEY 並複製第三方串接訊息後才完成。驗證綁定同一 KEY、endpoint、model／provider／native，變更後須重測。

新 KEY 預設包含兩來源所有已登錄模型；舊限制 scope 不擴權。完整 KEY 只在本次畫面 RAM／剪貼簿，關閉清空，不自動撤銷／重發。既有安裝首次升級出現精靈，**既有 API 繼續供應**，不自動建立 KEY、配對或改電源。可明確暫存後進主畫面調整模型／CLI；未完成時下次續接。

完成狀態跟隨同一 profile 的 device ID，正常來源更新／重啟不重跑。`mac_service.py onboarding-open` 可重開；`onboarding-status` 只讀 metadata。完成不是永久健康證明。

## 電源與還原

Mac 適配僅執行固定的 `pmset -c sleep <整數>`，以 `pmset -g custom` 逐項讀回。首次寫入前將原 AC sleep 存到 owner-only data 的 `macos-power.json`。取消授權／讀回失敗不宣稱通過，中斷後保留原值供重試／還原。只有本人點選授權按鈕才顯示系統管理員對話框，不保存密碼。

還原只回復原 AC sleep。owner 已自行改成其他 sleep 值時拒絕覆寫。全機電源資源請勿由多 profile 同時管理。開發測試使用 fake adapter，不偷偷改工作站電源；組織政策由裝置管理員處理。

鎖定與系統睡眠不同：使用者仍登入、Keychain 可用、網路正常且主機未睡眠時，背景 Bridge 可推論。闔蓋、手動睡眠、登出、關機或斷電仍會中斷。LaunchAgent 不代表開機未登入即可供應。

## 來源更新及回復

先在本機來源 checkout 同步、審查及測試，再使用安裝內工具：

```sh
# BRIDGE_PY、BRIDGE_APP 依原 source-install.json 欄位填入。
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" update --source /path/to/reviewed/source
```

管理台「排空並從本機來源更新」只用安裝器記錄的 `source_checkout`，不接受網頁傳入任意來源，不自行抓取／合併遠端。依序 pause／wait-idle、停止本 profile、保留 manifest／舊 app、安裝、啟動及確認 HTTP 版本；失敗嘗試還原原 manifest 並啟動舊版。手動實例持有 lock 時拒絕更新，不強殺程序。

此為明確操作的來源更新，沒有 Mac 簽章 feed、強制最低版本或公發安裝包。Windows Ed25519／Velopack 政策不適用 Mac。依賴不相容的大版本仍須依 [回復說明](CROSS-PLATFORM-INSTALL.md#macos-launchagent-管理與回復) 恢復對應 runtime；程式回復不代表資料庫回復。

## 儲存邊界

`macos-onboarding.json` 只存 installation ID、完成時間／版本、power_consent、key ID 與 allowlist 驗證收據。`macos-power.json` 只存原 AC sleep、pending／enabled 狀態。均不含 KEY、CLI stdout 或原始內容。裝置 secret 仍在原使用者登入 Keychain，SQLite 只存 KEY hash 與 metadata。更新保留 endpoint、device ID、有效 KEY、模型、推論容量與紀錄。
