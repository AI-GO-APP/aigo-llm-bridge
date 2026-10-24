# Mac 排隊與 Decisions 階段 0–2：候選證據

日期 2026-10-24（Asia/Taipei），候選 0.9.7-mac.1，基線來源 main 5d5e406。範圍為 [#36](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/36)，門檻固定於 [效能計畫](../PERFORMANCE-PLAN.md)；warm CLI 池另列 #39。

本文件只記實際證據。Source 實作、單元／HTTP 回歸、deterministic 基準、真訂閱、HTTPS、Release 與正式安裝為不同層。未通過的欄位不能用相鄰層證明。

## 狀態

| 層次 | 本輪證據 |
|---|---|
| Source | 已實作可取消 FIFO、受理預算、容量設定、numeric timings、固定 Decisions 驗證；原始碼候選 |
| 回歸／維護 | 執行中，完成後補命令與數量 |
| 合成基準 | 執行中；替身 runner，不啟動訂閱 CLI，真 schema 子程序與 HTTP |
| 真訂閱 3 輪混合 64 | 未驗；不將合成數字當訂閱收益 |
| 公開 HTTPS 64 | 未驗；不以 health／401／本機成功替代 |
| Mac Release／正式更新 | 未執行；保留原正式 profile／URL／KEY／CLI 登入 |
| Windows | 僅共用 source 回歸；沒有原生安裝／發布證據 |

原工作區的 AGENTS.local.md／.codex/config.toml 及未提交 owner 變更未帶入工作樹或發布包。未操作電源、鎖定、訂閱登入、Cloudflare 帳單或其他 Cloud 專案。

## 合成 HTTP 基準（第一組完整矩陣）

固定 runner 每題 0.5 秒，CLI 不啟動；舊版 schema 使用真 Python 子程序。baseline／candidate 各 45 輪、2,880 筆，共 5,760 筆全部正確，model／receipt／cost／call counts 一致，均在 38 秒內。workers 32／48／64；Chat-only、Decisions-only、混合；單題／三題；每配置三輪。

下表為混合負載三輪中位數；**這是合成機制比較，不是真訂閱吞吐**。

| workers | 每筆 Decisions 題數 | Decisions p95 基線→候選 | Chat p95 基線→候選 | good RPM 基線→候選 |
|---|---|---|---|---|
| 32 | 1 | 1.989→1.085 s | 0.554→1.083 s | 1904.51→3463.08 |
| 32 | 3 | 4.088→3.083 s | 0.555→2.070 s | 911.77→1235.21 |
| 48 | 1 | 1.707→1.069 s | 0.545→1.068 s | 2136.83→3494.70 |
| 48 | 3 | 3.920→2.075 s | 0.552→1.064 s | 936.17→1828.87 |
| 64 | 1 | 1.801→0.578 s | 0.557→0.572 s | 1821.79→6524.95 |
| 64 | 3 | 3.477→1.581 s | 0.553→0.563 s | 888.48→2407.87 |

64/64 混合單題 Decisions p95 下降約 68%，三題下降約 55%；Chat 增幅約 2.6%／1.8%，符合合成門檻。同配置 peak tree RSS 從約 148–153 MiB 降至約 54 MiB。32／48 使較快完成驗證的 Decisions 也進 FIFO，占用第一批執行數，部分 Chat 等下一批；其 Chat p95 超過 +10% 門檻，故**不採為新預設**，保留 64/64。不能用總吞吐變好掩蓋 Chat 延遲。

最初候選曾因 notify_all 喚醒閒置 workers，讓 Chat p95 超過門檻；已改單次必要喚醒。完整矩陣採修正後排程。後續 wall-clock／錯誤物件生命週期強化另跑最後候選的 64 配置核實，不把前期調校輪次冒稱最終來源。
