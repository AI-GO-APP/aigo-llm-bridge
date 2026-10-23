# Windows 0.8.0 onboarding 候選驗收

目前階段：實作與隔離驗證中，**尚未發布／未升級正式 Windows**。原正式 0.7.3 與其先前已知 Worker 500/1101 是不同狀態；本輪不修／不部署該 Cloud，也不改正式機電源或既有 Claude Code。

| 案例 | 狀態／邊界 |
|---|---|
| 新 profile 必須 onboarding、完成後日常跳過、升版保留、重裝安裝 ID 改變 | fake coordinator 回歸通過，原生 Setup／update 另記 |
| 訂閱 ready 不重新登入、active request 拒絕登入 | fake process／status 回歸通過；未對目前 Claude 執行登入／登出 |
| Cloudflare 帳戶選擇、錯帳戶拒絕、無憑證 AI IDE prompt | adapter 回歸通過；未對正式 Worker 變更 |
| 新 KEY 全來源、一次交付、完成檢查、metadata only | 隔離 Store＋adapter 回歸通過；真 Cloud OAuth／BYO 另驗 |
| 缺失／布林／字串／負／NaN／Infinity cost 不通過 | HTTP adapter 回歸通過，包含 GET→POST 順序；不算真供應商 inference |
| AC-only、DC 原值、鎖定原值、失敗 rollback、組織限制、不覆寫 owner 新計畫 | fake native adapter 回歸通過；owner 工作站無電源寫入 |
| UAC 同意／取消、alternate admin 的 HKCU 分離 | 未有真人 UAC 操作證據 |
| 真 Windows runner 電源套用／還原 | 待 CI；只在可拋棄 GitHub-hosted runner 執行 |
| 真 Setup→A→B、renderer 五步、重啟／更新不重跑、URL／KEY／資料不變 | 待 native acceptance |
| 本人 CLI／Cloudflare OAuth、一鍵新 Worker、真 LLM PONG／cost、實體拔插電／待機 | 未驗；需指定乾淨安裝者環境，不能以 mock 或既有登入代替 |

文件：[ONBOARDING](../ONBOARDING.md)、[CI-CD](../CI-CD.md)、[RELEASE](../RELEASE.md)；需求 R-14～18、決策 D-16～20。發布／正式已安裝需通過相應閘門後另記，不能把候選版號當作完成。
