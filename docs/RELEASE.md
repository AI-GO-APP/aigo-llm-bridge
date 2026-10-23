# Windows Release 操作手冊

此文件針對 Windows PyInstaller＋Velopack internal。產品文件入口見 [README](README.md)，檢查矩陣見 [CI-CD](CI-CD.md)；Mac 與安裝者 Worker 由各自維護者／擁有者處理，不共享此發布指令。

## 一次性發布環境

- repo 可匿名讀取 Windows Release assets；安裝者不需 PAT。若原碼改 private，先遷移到公開專屬更新儲存來源，不將發布 token 塞進包。
- repo variable `BRIDGE_WINDOWS_UPDATE_PUBLIC_KEY` 為 base64 Ed25519 32-byte 公鑰。
- environment `windows-internal` secret `BRIDGE_WINDOWS_UPDATE_PRIVATE_KEY` 為其對應私鑰。安全備份由發布者管理；不得重產生取代既有公鑰，不提交到 repo／log／Release。
- 保留 repository secret `BANNED_TERMS`。沒有 Windows Authenticode 公發憑證，internal notes 必須如實標示；Ed25519 用於更新資料驗證。
- builder 使用 workflow 內固定 runtime 與 `packaging/windows/requirements-lock.txt`；本機若用 vpk.dll 可透過 `dotnet <vpk.dll>`，不是浮動 latest。

## 正常功能發布

1. 確認 Windows 範圍，更新 `packaging/windows/release-target.json` 與 CHANGELOG。共用 core 或 Mac 若未修改不升其版本；完整走需求／decision／驗收文件。
2. 以合成 profile 做隔離 Setup、原生功能、A→B，另外記錄目前正式環境的已知故障。沒有權限對正式機改電源／登入／Worker時，以隔離或拋棄 runner 驗，不擅自動它。
3. PR 的 Windows 相關 CI 通過，squash merge main。核對 main SHA、來源 clean、QA 的 source/fixture 範圍；未驗的真 OAuth／BYO／power 桌面行為明列，不套用其他版本結果。
4. 在 main 執行下列 CLI（本機 `gh` 必須有此 repo 操作權，安裝者不需要）：

```powershell
gh workflow run windows-installer-publish.yml --repo AI-GO-APP/aigo-llm-bridge --ref main -f announce=true -f minimum_version=0.7.0
gh run list --repo AI-GO-APP/aigo-llm-bridge --workflow windows-installer-publish.yml --limit 5
gh run watch <本次 run ID> --repo AI-GO-APP/aigo-llm-bridge --exit-status
```

`announce=false` 僅建立候選 artifact。`announce=true` 仍會先完整 package／native gates，失敗不宣布。不要同時發兩個相同 Windows 版本；發布 workflow 已序列化。這不是部署 Cloudflare，也不觸發 Mac release。

5. 核對每版 tag `windows-installer-internal-v<版本>` 的 Setup、full nupkg、feed、artifacts.json、self-test.json，以及固定 tag `windows-updates-internal` 的 `windows-x64-internal-policy.json`。發布器已匿名下載回讀，維護者仍要讀 receipt／結果，不只看 run green。
6. 日常更新入口排空原 Bridge → 備份 SQLite／DPAPI／onboarding／power → 停自有 service/viewer → Velopack 替換 → 同 data-dir 重啟。確認原 KEY 可用、URL/device ID/hash/metadata 不變、安裝版本／commit 正確、完成者精靈未重開、未擅自部署或重新登入。
7. 更新 `docs/qa/<日期>-<版本>-windows.md`、[ACCEPTANCE](ACCEPTANCE.md)、Release notes，再以文件 PR merge。報告區分本機 API、外部 Worker HTTPS、真 LLM、UI、native permissions；不放完整 KEY／token／原始內容。

## Policy-only：強制更新及續期

已宣布版本 B 不重建，只提高最低版本或續簽有效期：

```powershell
gh workflow run windows-installer-publish.yml --repo AI-GO-APP/aigo-llm-bridge --ref main -f announce=true -f published_version=<已發布B版號> -f minimum_version=<最低允許版號>
```

版本、commit、release URL、full/feed SHA256 固定；序號遞增，不降已知 minimum。相同內容安全重試；policy 三十天有效、到期前七天可續期。新 floor 會停新工作，不殺已執行推論；未知新 policy 的離線安裝不能遠端知道要更新。已快取最低限制不因斷網／過期而消失。

## 故障處理

| 故障 | 行動／不可做的事 |
|---|---|
| CI／native gate 失敗 | 讀具體錯誤與 acceptance JSON，修原因、提高必要版號再驗。不忽略某平台未驗，不能用 mock 通過冒稱真權限成功。 |
| package 成功、announce 失敗 | 先核對有無 public immutable version／policy；相同版本同 bytes 可安全重試發布器。若需要改 code／包用更高版號，不覆寫舊同版檔案。 |
| GitHub assets 404／匿名不可達 | 不宣布；先修 public assets 可讀性／網址。不要把 PAT 交給所有安裝者。 |
| signer 不符／hash 不符／序號倒退 | 保持舊服務，不繞過驗證；核對原 signer、公鑰、不可變 asset。將不一致視為失敗，不能加 verify=false。 |
| 排空超時 | 保留正在執行工作並恢復原接單設定；未知結果不可重送。 |
| apply／重啟失敗 | 保留 pending.json／原 metadata 備份。只在原版本原 schema 允許 `update recover` 恢復接單；不得把舊 DB 備份覆蓋新版。若版本或 schema 已變更，出更高版修復。 |
| 訂閱登入失效 | 依本人 CLI 授權流程處理；不換 Worker／URL／client KEY。 |
| Worker health 500／1101 或離線 | 與 installer 更新分開記錄；Windows 成功不能宣稱 Cloud 已好。安裝者確認自有帳戶與原 Worker後另行處理，不未經授權重建或更動另一團隊 Cloud。 |
| 精靈中途關窗／重啟 | 沿用同一 profile，重新檢查；保存的 KEY 可貼回繼續真 POST。不自動重播部署／推論，也不自動輪替 KEY。 |
| 電源權限不足／組織休眠政策 | 安裝保持未完成，找裝置管理員。按原備份還原，不關閉 UAC／MDM，保留鎖定；不假報永不休眠。 |

## 發布收據 checklist

- [ ] Windows 版本、core 版本、commit、branch/main ancestry、pack ID、channel、dirty=false、redistributable=true。
- [ ] PR 與相關 CI run URL、測試數、未驗範圍、native Setup／update／power receipt、測試 profile 與正式 profile 區別。
- [ ] Setup／full／feed 大小及 SHA256、公鑰 fingerprint、policy sequence／minimum／expires、公開匿名回讀。
- [ ] 安裝版前後版本及 commit、原 URL/device/KEY/hash/DPAPI/metadata、完成精靈狀態、啟動與已知外部故障。
- [ ] 測試 KEY 撤銷；正式交付 KEY 有效且由擁有者保存；不把兩者混淆。
- [ ] Release notes／QA／ACCEPTANCE 與隨包文件同步。公發簽章與未驗 Mac／Cloud 不列通過。

所有檔案與終端 log 都只允許中繼資料，不為了 release debug 加入原始 request/response、完整 client KEY、DPAPI 明文或 provider auth。

Windows 0.8.1 的安全邊界、依賴與 Schema／CLI 傳輸限制見 [SECURITY](SECURITY.md)；更新不重新授權 CLI、不重建 endpoint 或 KEY，也不自動部署 Worker。
