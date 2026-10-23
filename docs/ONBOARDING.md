# Windows 首次安裝 onboarding

適用 Windows Velopack 0.8.0；發布狀態與實測範圍，見 [ACCEPTANCE](ACCEPTANCE.md)。本文件是操作契約，不能當成驗收通過證明。macOS 的安裝／權限／發布由其維護者另行處理。

## 安裝者的完整路徑

1. 先依 [BYO 準備事項](BYO-QUICKSTART.md) 備妥 Node.js 22+，在新開啟的終端機確認 `node --version`，再下載並啟動 Windows Setup；先安裝前置工具可避免背景程式沿用舊 PATH。核對 [Release](RELEASE.md) 的公開附件、大小／SHA256。現階段未有 Authenticode，依自己裝置政策確認未知發布者；不要停用系統防護。
2. 執行 Setup，首次開啟管理視窗進入五步精靈。可關閉整個視窗稍後續接；已完成安裝後正常啟動不再彈出，可從「連線與設定 → 安裝設定精靈」手動重開。
3. 明確同意此電腦只調整插電自動睡眠／休眠，再按套用。鎖定、螢幕及實體按鍵設定保留。程式先保存原值、建立專用計畫、只改 AC 索引，逐項讀回；不會因單純開啟安裝包就修改電源。
4. 檢查本地 LLM CLI。預設 Codex／ChatGPT 訂閱；Claude 選用，至少一來源可用。不需要將供應商憑證輸入 Bridge。
5. 安裝 Node.js 22+、Wrangler 4.95.0，以自己的瀏覽器完成 Cloudflare OAuth。明確選定自有 account ID。
6. 選「一鍵部署並綁定」，或把「AI IDE 協作 prompt」貼給自己的 AI IDE。完成後重新檢查，確認固定 workers.dev endpoint、裝置已配對與 Relay 在線。
7. 建立長效 KEY（預設 Claude／Codex 模型全開），保存到自己的服務端 secret，複製含 endpoint、KEY、model 與相容限制的第三方串接訊息。不要保存到公開 repo 或前端 bundle。
8. 選擇自己訂閱可用的模型，明確發出一次合成 HTTPS 測試。先 GET models，再 POST chat/completions；需回 PONG 且 `usage.cost` 是有限、非負數值。使用少量訂閱額度，未知結果不自動重試。失敗時留在精靈排錯，不能宣稱完成。
9. 勾選已保存 KEY／交接訊息，按完成。交付模型及 native/provider 對應必須與本次真 HTTPS 測試相同，修改後需重新測試。完整 KEY 只在 RAM／剪貼簿，關閉精靈便清空；中途重啟需貼回已保存的 KEY 再測一次，不自動建立或撤銷 KEY。

目前精靈會顯示 CLI 安裝命令並啟動已安裝 CLI 的官方登入；**不自動安裝 Node/npm 或取得供應商密碼**。需新安裝 CLI 的人可自行依命令安裝，也可交給 AI IDE 完成。登入瀏覽器頁面仍由本人同意授權，一鍵 Worker 部署不代表能略過 OAuth。

可按「暫存進度，前往進階設定」使用完整管理台，調整訂閱可用的模型／原生 ID 或 CLI 路徑，再從安裝精靈按鈕返回；這不會把安裝標示完成，下次啟動仍需續接。若在 Bridge 已啟動後才安裝 Node／CLI，從主畫面「結束 Bridge」正常停止，再由 Windows 捷徑重新開啟，讓新 PATH 生效；關視窗仍常駐，不能用關窗代替停止。Windows PowerShell 若擋 npm／CLI 的 ps1 wrapper，可用同套件的 npm.cmd／wrangler.cmd／codex.cmd，不需要降低 ExecutionPolicy。

## 訂閱 CLI 授權

Codex：先依 [OpenAI 官方驗證說明](https://developers.openai.com/codex/auth/) 安裝／使用 CLI。

```powershell
npm install -g @openai/codex
codex login
codex login status
```

選 ChatGPT 訂閱登入，不選 API key。瀏覽器 callback 受限時，官方另有 `codex login --device-auth`；由本人啟用並完成，不把 auth.json 提供給 Bridge／發布者。精靈只呼叫 `login status` 判斷來源，不以狀態檢查假裝已驗證模型／額度；最終 HTTPS 合成 POST 才證明當下可呼叫。

Claude Code：依 [官方安裝說明](https://code.claude.com/docs/en/setup) 安裝，再使用 [CLI auth 指令](https://code.claude.com/docs/en/cli-reference)：

```powershell
claude auth login
claude auth status
```

Bridge 接受 Claude.ai 訂閱登入。任一來源已就緒就沿用，不自動 logout/login、不操作既有終端機、不修改全域設定。有 Bridge 工作進行中拒絕發起來源登入；切換帳號另依 [裝置生命週期](DEVICE-IDENTITY.md) pause → wait-idle → 本人登入 → 檢查 → resume。其他程式的工作不在 Bridge 的佇列內，操作前仍由本人確認。

CLI 不在 PATH 時，在精靈步驟 2 的進階區指定原生 `.exe`。腳本入口會嘗試解析其 npm 套件原生執行檔，不透過 shell 執行任意字串。變更 CLI 路徑只影響 Bridge；不更改使用者已開啟的 CLI 程序。

## Cloudflare：一鍵或 AI IDE

依 [Wrangler 官方 OAuth／whoami 說明](https://developers.cloudflare.com/workers/wrangler/commands/general/)：

```powershell
npm install -g wrangler@4.95.0
wrangler login
wrangler whoami --json
```

登入仍由本人在瀏覽器核准。Bridge 只保留 allowlist 的 account ID／名稱供選擇，不保存 CLI 原始 stdout、email 或 OAuth token；Wrangler 自己保管其授權。即使只有一個帳戶，首次部署仍須明確選定並勾選自有帳戶部署授權。

「一鍵部署」沿用 `byo.configure → Cloudflare.verify → publish`：產生此裝置的本機專案、核對登入帳戶、部署、加密 pending 憑證、設定 Worker secret、實際 HTTPS 配對驗證、提交原 profile。重試不刪除 pending 或換 URL，既有帳戶／Worker／endpoint 不符便拒絕。Cloudflare Free 方案仍可能要求本人完成帳戶的 Workers 設定或接受適用方案；程式不購買、不代辦付款。

AI IDE 模式會產生**這個安裝位置與原 data-dir 專用**的 prompt。它要求先讀隨附指南／BYO skill，用 `aigo-bridge.exe byo plan/deploy/status`，明確帳戶及同一 profile。使用者可透過 AI IDE 協作，不必安裝第二個模型 CLI 當作部署 agent。prompt 不含 client KEY、裝置配對 secret、Cloudflare token 或供應商憑證。產生 prompt 不代表已部署或授權其他 Cloud 專案。

若 AI IDE 在外部 CLI 完成部署，回精靈重新檢查；服務以同一 SQLite／DPAPI 讀取設定並重新啟動 Relay。若 URL 是已配置的正式入口，不能以「測試」名義換網址、重建 Worker 或修復其他團隊正在管理的 Cloud。

## 插電不自動睡眠／休眠，保留鎖定

Windows 鎖定與休眠是不同狀態。API 的目標是主機持續運作，不要求桌面持續解鎖。候選已取消所有禁止鎖定的設定；本機真鎖定驗收狀態見 [鎖定 QA](qa/2026-10-23-windows-locked.md)，不得以文件或單元測試代替實測。

| 控制 | 實作範圍 |
|---|---|
| 插電 AC 自動睡眠 | 複製原電源計畫，只將支援的 sleep、hibernate、unattended sleep 設 0（永不）。至少 sleep 必須可控制；未支援項目列出，不宣稱已套用。逐項讀回 AC=0、DC=原值。 |
| 螢幕與鎖定 | 不更改 display／locked display、螢幕保護、動態鎖定、登入密碼、Win+L 或組織鎖定政策；沒有相關登錄寫入及常駐取消鎖定程序。 |
| 闔蓋／睡眠鍵／電源鍵 | 保持原動作；若原本會睡眠或關機仍會中斷 API。需要常駐 API 時請保持主機實際運作，另依裝置政策管理。 |
| 電池 DC | 不更改全部 DC 索引，也不在拔電時更改使用者設定。 |
| 備份與還原 | `windows-power.json` schema=2 保存原計畫、專用 GUID、三項原 AC/DC 及 unsupported。不含 HKCU 值或憑證。還原原計畫；若 owner 已改選其他計畫，不擅自切回。 |
| 組織休眠政策／廠商工具 | 不覆寫強制 AC 休眠政策；受限時保持安裝未完成，由裝置管理員處理。組織鎖定政策不阻擋這個步驟。廠商另行觸發的睡眠需實機驗證。 |
| 登出、手動睡眠／休眠、關機、斷電、Windows 重啟 | 不攔截。URL／KEY 持久不表示主機關機或使用者尚未登入仍能推論。鎖定不可當成登出。 |

優先使用一般權限。只有電源計畫 ACL 不允許修改時，才由本人明確點選「電源權限不足時以管理員套用（UAC）」；不是為了禁止鎖定而提權，也不要求所有安裝者都通過 UAC。helper 僅處理三項電源設定／還原，從不寫原使用者或管理員 HKCU、不處理 LLM／Cloudflare 登入。取消或拒絕時保持未完成，禁止降低 UAC／企業防護。原值備份完成後才寫入，失敗嘗試還原，不假報成功。

管理台「還原原電源計畫」可取消，已套用的 AC 計畫在服務重啟後持續有效。電源計畫是 OS 共用資源，多 profile 同時管理尚未驗收，請勿同時啟用。開發期舊 schema=1 候選若曾套用，需先用原候選還原；新版偵測後拒絕直接覆蓋，以免遺失舊備份。這不影響正式 0.7.3，它沒有此電源功能。

目前不自動啟用 Windows 登入時啟動，可於管理台選用。程式不保存 Windows 密碼、不啟用自動登入；正常關閉視窗仍常駐，停止服務或登出後不再提供推論。

參考：[Windows AC 電源索引](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/powercfg-command-line-options)、[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)、[WTS 鎖定狀態](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ns-wtsapi32-wtsinfoex_level1_w)。鎖定探針使用暫時的 system-required，不要求 display-required，不改永久電源或鎖定政策。

## 何時重跑，什麼永遠保留

| 事件 | 精靈 | 裝置資料 |
|---|---|---|
| 新裝置／新 profile | 必須完成 | 新 device ID；沒有共享 endpoint／KEY。 |
| Setup 全新安裝／解除後重裝 | after-install hook 產生新 installation ID；重走精靈 | 原外部 data-dir 若保留，URL／KEY／metadata 不刪、不輪替。電源同意及實測不能偽造。 |
| 同一安裝日常啟動／關窗再開 | 完成者直接主畫面；未完成續接 | 不自動部署、不自動登入、不自動發 KEY。 |
| 正常 Velopack A→B 更新 | 保留原 installation ID 與完成紀錄，不重跑 | 同 profile、KEY、URL、授權及 metadata；更新備份包含 onboarding／power。 |
| 既有 0.7.x 升到首次提供精靈的版本 | 尚無紀錄者需跑一次；不憑舊 URL 當成已同意電源變更 | 既有服務／KEY／URL 保留，不因未完成精靈破壞原呼叫。 |
| CLI 訂閱登出／切換 | 不重建安裝，來源變未就緒由主畫面處理 | 裝置資料維持。 |

完成紀錄不是安全授權，也不是永久健康證明。日後來源登入、Worker、電源或網路失效在主畫面顯示，不自動重播安裝的授權／部署。新一輪真 POST 需本人明確點選。

CLI 可使用 `aigo-bridge.exe onboarding open --data-dir <原目錄>` 開啟精靈，`onboarding status` 只回傳中繼資料狀態。進階 `setup`／`byo` 工具仍可用，但單純部署成功不會略過精靈最後的電源及交付驗證。

## 驗收與限制

測試分開記錄：fake adapter 規則測試、隱藏真 WebView renderer、真 Setup／A→B、可拋棄 Windows runner 的真電源套用還原、安裝者真 OAuth／BYO／LLM HTTPS。前四者不能冒稱第五者已完成。測試內容、狀態與發布流程見 [CI-CD](CI-CD.md)、[Release](RELEASE.md) 與 [本輪 QA](qa/2026-10-23-windows-onboarding.md)。本輪不修改目前使用者正式 Windows 的電源／登入，也不部署其正式 Worker。
