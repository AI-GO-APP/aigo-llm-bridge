# Windows 鎖定但不休眠：真實 Codex 驗收

目前狀態：**基準推論已通過，人工 Win+L／解鎖尚待完成，不能宣稱鎖定期間已驗收**。正式 Windows 0.7.3、既有 Claude Code 登入、Cloudflare 部署及永久電源／鎖定設定均未修改。

## 測試方法

`tools/verify_windows_locked.py` 啟動獨立 data-dir 的 Windows frozen 候選，建立測試 KEY，使用現有 Codex 的 ChatGPT 訂閱。CLI 的登入狀態與推論都走背景程序，不操作或重新登入 Claude。測試 KEY 只在 RAM，最後撤銷；只保存 HTTP 狀態、模型、時間、token、成本與通過條件等 metadata。

測試由本人按 Win+L、之後正常解鎖；探針不自行鎖定、解鎖、登出或更改 Windows 密碼。透過 WTSQuerySessionInformationW 的 WTSSessionInfoEx / SessionFlags 每 0.5 秒讀取同一 OS session 的鎖定狀態，不能只以 LockWorkStation 回傳成功當作鎖定證據。

同一個 frozen Bridge／KEY 執行四輪標準 GET models＋POST chat/completions：解鎖基準一輪、鎖定兩輪、解鎖後一輪。鎖定階段至少跨 75 秒，避免只覆蓋瞬間鎖定；每輪要求 WTS 全程符合預期、PONG、正 token 與有限正數 `usage.cost`，成本來源須為 OpenRouter 牌價估值。超時或任何鎖定狀態改變均不通過。這是本機 API＋真 Codex 訂閱路徑，**不等同 Cloudflare 外部 HTTPS 路徑已通過**。

探針暫時呼叫 SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) 排除自動睡眠干擾，未要求 ES_DISPLAY_REQUIRED、未修改永久電源計畫或鎖定登錄值；finally 清除暫時要求。畫面仍可關閉、系統仍可鎖定。這與安裝者 AC 三項持久電源設定的 runner 驗收分開。

## 本輪結果

| 階段 | 狀態 |
|---|---|
| 解鎖基準 | 已通過：frozen 0.8.0 候選 R7（來源 76a9c5c），openai/gpt-6-astra、HTTP 200、5,564 ms、prompt 8,542／completion 6 tokens、usage.cost 0.08572 USD（牌價估值）。 |
| 鎖定第一／第二輪 | 等待人工 Win+L；目前沒有通過證據。 |
| 解鎖後與同 KEY／設定保留 | 待前一步完成。 |

本機僅 metadata 收據位於 ignored `.desktop-build/locked-acceptance-r1/acceptance.json`；是否最終成功以 `success=true` 且四輪／全部 checks 通過為準。單筆 HTTP 200 或 ready 狀態不算完成。等待逾時會失敗並撤銷測試 KEY、正常停止隔離服務，不會使用新 KEY 自動重跑推論。

## 候選調整與發布閘門

依使用者最新指示，候選只調整插電自動 sleep／hibernate／unattended_sleep；移除 HKCU 鎖定寫入、背景鎖定 guard、禁止鎖定同意及手動鎖定檢查門檻。螢幕、鎖定、實體按鍵、DC 保留。先一般權限，電源 ACL 不足時才由本人選用 UAC。規格見 [ONBOARDING](../ONBOARDING.md)、需求 R-16、決策 D-21。

鎖定實測與修訂後 native runner 尚未通過前，不把舊版含鎖定調整的候選發布或升級正式電腦。首次 OAuth／自有 Worker 部署的安裝者驗收仍是獨立缺口，不能用目前既有 Codex 登入替代。

參考：[WTSINFOEX_LEVEL1_W](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ns-wtsapi32-wtsinfoex_level1_w)、[LockWorkStation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-lockworkstation)、[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)。
