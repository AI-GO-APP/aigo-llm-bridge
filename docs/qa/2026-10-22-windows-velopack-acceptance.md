# Windows PyInstaller／Velopack 隔離安裝與更新驗收

範圍：Windows x64 internal 安裝器、frozen CLI、自建簽章更新政策、原生 A→B 更新、資料保留及 CI/CD。未操作正式 Windows 安裝，未改 Worker、Mac 或 AI EA Cloud；未宣布公開更新。

## 建置基準

- 程式 commit：`7baad911c9f51ad1a001058eb1c2b2330f9eeae2`，A／B manifest 均為 `dirty=false`。
- Windows 11 x64；Python 3.14.3、PyInstaller 6.22.3、hooks 2026.8、Velopack Python／vpk 1.2.161；完整依賴見 packaging/windows/requirements-lock.txt。
- A：Windows package 0.7.0；B：0.7.1；兩者核心版本仍為 0.6.5。
- 獨立 LocalProbe package ID、臨時 Ed25519 公鑰、loopback 更新站與獨立 profile；Setup 真正執行，更新由原生 Velopack 下載、安裝及重啟，非 mock installer。
- 測試用 URL 為合成固定設定；沒有測試新外網 HTTPS／供應商訂閱推論，不能把本報告當作該兩項驗收。

## 最終結果

工具：`tools/verify_installer_update.py`，輸出 `.desktop-build/native-update-acceptance-final/acceptance.json`，22／22 checks 通過。

| 實測 | 結果 |
|---|---|
| Setup 靜默安裝至指定隔離路徑，產生 Update.exe／current | 通過 |
| 真 frozen console CLI 建立 Codex scope KEY | 通過；明文只在驗收程序記憶體 |
| 舊 install.json 設定檔接管及安裝根目錄綁定 | 通過；沿用原 UUID／data-dir |
| setup 引導輸入空值正常退出 | 通過；未部署、未更改登入 |
| A 以原 KEY 呼叫真本機 HTTP models | 通過 |
| 自建 policy 宣布 B，A 偵測新版本 | 通過 |
| 壞簽章、feed hash 不符 | 拒絕更新，A 仍可認證呼叫 |
| 有合成 running 工作時 apply 等待逾時 | 延後更新並恢復原接單狀態 |
| 原生更新器下載 B、套用並啟動 B | 通過；frozen CLI version 與 startup acknowledgement 均為 0.7.1 |
| B 使用完全相同的原 KEY 呼叫 models | 通過；沒有建立替代 KEY |
| 原 device_id、URL、KEY hash、DPAPI 憑證 | 均保留 |
| 合成 metadata 的 token、cost 與接單設定 | 均保留 |
| SQLite backup、KEY 不以明文落 profile 磁碟 | 通過 |
| 正常停止後執行原生解除安裝 | 程式移除、profile 保留 |
| 測試 KEY 撤銷與測試程序清理 | 通過；不撤銷任何正式 KEY |

最終 B Setup：33,264,206 bytes；SHA256 `241d6a8d94ad7fae6f730f9addd4973837351090e1299eed5586b8d828bd46e0`。此包是不可分發的 LocalProbe，不上傳公開 Release；臨時 feed 已停止，不能作正常使用者的更新入口。

第一輪已實際升到 B，但驗收腳本誤以為 native apply 必定輸出 JSON，因 CLI 正常退出交給 updater 而失敗。修正為檢查真正的新版程序／完成紀錄；第二輪 18 項及最終乾淨來源的 22 項均通過。第一輪測試安裝亦已正常移除。

## 回歸與 CI/CD 邊界

- `python -m pytest desktop_bridge/tests packaging/windows/tests tools/tests -q`：161 passed、1 macOS-only skip。
- `node --test cloudflare/test/relay.test.js`：7 passed。
- Windows-only 版號 gate、JS 語法、版本一致性、私有字詞與機敏資訊掃描通過。
- `windows-installer.yml` 對 PR 執行相同原生安裝／更新驗收；CI 結果以 PR checks 為準，不以本機成功推定 runner 成功。
- `windows-installer-publish.yml` 已提供 main 手動建置與明確 announce 選項，預設不宣布。首次公開宣布前仍須配置專屬更新公鑰／簽署 secret 並執行發布與匿名下載回讀閘門；本輪沒有執行公開 announce。
- 沒有 Authenticode 公發憑證；更新 policy 簽章不會消除 Windows SmartScreen／企業政策限制。本機既有使用者的隔離安裝不等於乾淨 VM 或所有 Windows 安全政策已驗收。

操作、版本身份、遷移及恢復限制見 [Windows 安裝與更新](../WINDOWS-INSTALL-UPDATE.md)。
