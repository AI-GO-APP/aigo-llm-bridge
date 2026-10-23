# Windows 鎖定但不休眠：真實 Codex 驗收

目前狀態：**鎖定前一筆、鎖定中兩筆真 Codex 呼叫均通過，鎖定不會阻止此路徑推論**。原四階段腳本等待本人解鎖超過 10 分鐘後安全結束，因此整份四階段收據 success=false；解鎖後階段仍未通過，不得寫成完整四階段成功。正式 Windows 0.7.3、既有 Claude Code 登入、Cloudflare 部署及永久電源／鎖定設定均未修改。

## 測試方法

`tools/verify_windows_locked.py` 啟動獨立 data-dir 的 Windows frozen 候選，建立測試 KEY，使用現有 Codex 的 ChatGPT 訂閱。CLI 的登入狀態與推論都走背景程序，不操作或重新登入 Claude。測試 KEY 只在 RAM，最後撤銷；只保存 HTTP 狀態、模型、時間、token、成本與通過條件等 metadata。

一般使用探針由本人按 Win+L、之後正常解鎖。本輪依使用者要求與先前 Bridge 專用桌面安排，由代理另行呼叫一次 LockWorkStation 提出鎖定；探針本身不鎖定、不解鎖、不登出或更改 Windows 密碼。透過 WTSQuerySessionInformationW 的 WTSSessionInfoEx / SessionFlags 每 0.5 秒讀取同一 OS session 的鎖定狀態，不能只以 LockWorkStation 回傳成功當作鎖定證據。

同一個 frozen Bridge／KEY 執行四輪標準 GET models＋POST chat/completions：解鎖基準一輪、鎖定兩輪、解鎖後一輪。鎖定階段至少跨 75 秒，避免只覆蓋瞬間鎖定；每輪要求 WTS 全程符合預期、PONG、正 token 與有限正數 `usage.cost`，成本來源須為 OpenRouter 牌價估值。超時或任何鎖定狀態改變均不通過。這是本機 API＋真 Codex 訂閱路徑，**不等同 Cloudflare 外部 HTTPS 路徑已通過**。

探針暫時呼叫 SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) 排除自動睡眠干擾，未要求 ES_DISPLAY_REQUIRED、未修改永久電源計畫或鎖定登錄值；finally 清除暫時要求。畫面仍可關閉、系統仍可鎖定。這與安裝者 AC 三項持久電源設定的 runner 驗收分開。

## 本輪結果

| 階段 | 狀態 |
|---|---|
| 解鎖基準 | 已通過：frozen 0.8.0 候選 R7（來源 76a9c5c），openai/gpt-6-astra、HTTP 200、5,564 ms、prompt 8,542／completion 6 tokens、usage.cost 0.08572 USD（牌價估值）。 |
| 鎖定第一輪 | HTTP 200、PONG、5,402 ms、prompt 8,544／completion 6、cost 0.08574 USD；10 次 WTS 取樣全程 locked。 |
| 鎖定第二輪 | HTTP 200、PONG、8,272 ms、prompt 8,542／completion 6、cost 0.08572 USD；17 次 WTS 取樣全程 locked；鎖定測試階段累計 83.8 秒。 |
| 同 KEY 與資料 | 前述三輪使用同一測試 KEY，3 筆 completed／cost metadata 保留；原始測試內容沒有落入 profile 檔案。 |
| 解鎖後階段 | 本人尚未解鎖；等待 10 分鐘逾時。收據失敗原因是 TimeoutError，不是鎖定中 LLM 失敗；不重新鎖定、不假報第四筆。 |
| 清理 | 測試 KEY 已撤銷、隔離服務已正常停止、暫時防休眠要求已釋放；沒有永久電源或 UAC 設定檔。cleanup.json 6 項通過。 |

本機僅 metadata 收據位於 ignored `.desktop-build/locked-acceptance-r1/acceptance.json`；是否最終成功以 `success=true` 且四輪／全部 checks 通過為準。本輪 success=false 已保留，不為了局部成功改寫。`cleanup.json` 另存六項清理／metadata 檢查；不含完整 KEY。此時兩筆鎖定推論是實際成功證據，但不是第四階段已完成。

## 候選調整與發布閘門

依使用者最新指示，候選只調整插電自動 sleep／hibernate／unattended_sleep；移除 HKCU 鎖定寫入、背景鎖定 guard、禁止鎖定同意及手動鎖定檢查門檻。螢幕、鎖定、實體按鍵、DC 保留。先一般權限，電源 ACL 不足時才由本人選用 UAC。規格見 [ONBOARDING](../ONBOARDING.md)、需求 R-16、決策 D-21。

修訂來源 `926ab517f7535062e153a617be722c33ef69be9c`、[PR #15](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/15)：本機完整 Python **179 passed／2 skipped**、onboarding 30 案、relay 7、platform 2，docs／terms／secrets 通過。[一般 CI](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39884587415)、[Windows ZIP](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39884587710)、[Windows installer](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39884587369) 全通過。已下載並回讀 artifact：**8/8 AC-only 原生電源**（含套用中及還原後鎖定登錄不變、螢幕及實體按鍵 AC/DC 不變）與 **48/48 Setup A→B**。這些永久電源寫入只在可拋棄 runner，不在 owner 工作站。

正式 Windows 尚未升級；不發布舊版含鎖定調整的候選。完整解鎖後呼叫仍需補驗。首次 OAuth／自有 Worker 部署的安裝者驗收仍是獨立缺口，不能用目前既有 Codex 登入替代。

參考：[WTSINFOEX_LEVEL1_W](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ns-wtsapi32-wtsinfoex_level1_w)、[LockWorkStation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-lockworkstation)、[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)。
