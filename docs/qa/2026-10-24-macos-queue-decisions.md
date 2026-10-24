# Mac 排隊與 Decisions 階段 0–2：候選證據

日期 2026-10-24（Asia/Taipei），候選 0.9.7-mac.1，基線來源 main 5d5e406。範圍為 [#36](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/36)，門檻固定於 [效能計畫](../PERFORMANCE-PLAN.md)；warm CLI 池另列 #39。

本文件只記實際證據。Source 實作、單元／HTTP 回歸、deterministic 基準、真訂閱、HTTPS、Release 與正式安裝為不同層。未通過的欄位不能用相鄰層證明。

## 狀態

| 層次 | 本輪證據 |
|---|---|
| Source | 已實作可取消 FIFO、受理預算、容量設定、numeric timings、固定 Decisions 驗證；原始碼候選 |
| 回歸／維護 | 最終本機 Bridge＋tools 316 passed／18 skipped；Worker 13 passed；version／branding／product docs／secret scan 通過 |
| 合成基準 | 完整矩陣＋最終 64 配置＋三波持續負載，共 7,296/7,296 正確；HTTP／真 schema 子程序／替身 runner，未啟動訂閱 CLI |
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

## 最終來源與持續負載

Runtime commit `3749f90320189cbb369d94dd1317198285dff2cd`；選定與持續報告附 service／schema／decision／process／provider／store／budget 的 SHA256，已與最終 runtime 核對。所有合成 aggregate metadata 見 [JSON 收據](../concurrency-evidence/macos-queue-2026-10-24.json)。前期完整矩陣與最終來源報告分別標示，不捏造前期 hash。

完整矩陣後，最終來源另各跑 baseline／candidate 的 64 workers、單題／三題各三輪 burst，以及單題／三題各一組三波連續 64。全輪正確，沒有重送或 CLI 訂閱用量。

| 測項 | 題數 | Decisions p95 基線→候選 | Chat p95 基線→候選 | good RPM 基線→候選 |
|---|---|---|---|---|
| 三輪 burst 中位數 | 1 | 1.781→0.572 s | 0.552→0.573 s | 2086.66→6597.03 |
| 三輪 burst 中位數 | 3 | 2.890→1.593 s | 0.556→0.568 s | 1305.75→2391.51 |
| 三波連續合計 | 1 | 1.542→0.555 s | 0.544→0.552 s | 2334.84→6875.34 |
| 三波連續合計 | 3 | 3.127→1.585 s | 0.554→0.565 s | 1136.32→2422.12 |

最終 64 配置符合合成門檻：單題 Decisions p95 -67.9%、三題 -44.9%，Chat 變化 +3.8%／+2.1%；持續負載也符合。三波不是三輪中位數，表中明列合計。p50／p95／max／HTTP／38 秒與資源取樣保留在 JSON；第一組舊版完整矩陣未量 p50，最終選定及持續組已補齊，不反推缺失值。保留 64/64，不採低執行數。

## 測試與 CI 分層

- 本機 Python 3.12：`python -m pytest desktop_bridge/tests tools/tests -q` → **316 passed，18 skipped**；涵蓋受理前保留、32＋32／第 65 筆、1 秒內取消／撤 Key／逾時、3 MB queued spec 引用釋放、20 次滿載 health p95 <1 秒、FIFO、去重、stop 競態、worker 啟動失敗清理、設定第二筆寫入失敗的交易回復、終態收據失敗回 503 並釋放且不誤回成功、舊 profile、wall-clock 調整、外部惡意 regex、stdin 不讀取的逾時與 typed differential corpus。
- `node --test cloudflare/test/relay.test.js` → **13 passed**。version／lint_branding／check_product_docs／scan_secrets／git diff --check 通過。第三方 handoff 改用 profile 的實際 inference_pending；建立 Key 的說明改為受理總數，沒有新增前端功能。
- 本機 `lint_terms.py --require` 因缺私有清單失敗；前一 source commit 769d0bc 的 [CI](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40047968385) 中 lint-terms（--require）、secret／version／docs 檢查成功；不複製私有清單到工作樹。最終 PR head 另依實際 CI 結果更新。
- [Windows installer regression](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40047968384) 在核心測試前的鎖定依賴掃描失敗：未改動的 cloudflare/package-lock.json 含 undici 7.29.1，scanner 回報 GHSA-4qv8-2p9j-2685、GHSA-f72v-6w45-q472、GHSA-xjj6-f33q-929c。沒有移除 scanner、放寬門檻或更改 Windows 依賴；它是獨立的 CI 阻擋，不宣稱整體 CI 全綠。

PR 保持 Draft。真訂閱三輪、公開 HTTPS 64、Mac release／正式安裝仍未完成，不把本輪 source 實作當作正式交付，也不關閉 #36。

## 本機原生 UI 與第三方容量文案

`python tools/verify_macos_console.py --output /tmp/ltbb-queue-native-ui` → success=true。本次以隔離合成 profile 渲染六頁、light／dark、1200／480 寬及 Windows 適配卡；保留既有原生 Save／Cancel、CSV、剪貼簿還原、Key 關閉清除、外部導覽阻擋及關窗後服務驗證。所有布林檢查通過，並檢視四組六頁 contact sheet 與 Windows 卡；沒有操作 owner 的電源、登入或正式 profile。

第三方 handoff／管理／onboarding 針對性回歸另 41 passed／6 skipped；handoff 的 64 預設、舊 profile 2 容量與獨立 pending=32 皆正確，不能對較小容量仍交付固定 64。

[原生驗證 metadata](assets/mac-queue-ui-result.json)、[六頁淺色寬版](assets/mac-queue-light-wide.png)、[六頁深色窄版](assets/mac-queue-dark-narrow.png)、[Windows 深色窄版適配卡](assets/mac-queue-windows-card.png)。圖片全為合成資料，不含 owner Key／設定。這些是 renderer／adapter 證據，不替代 Windows 原生安裝。

最後硬化將 request budget 傳入 model discovery／auth status／牌價載入 timeout 與共用 metadata lock。新增短期限 cold-model／pricing lock 測試與 status timeout 測試，全部 408／零推論；可選 RAM availability evidence 不得蓋掉原錯誤。Windows adapter JavaScript tests 3 passed；handoff／前端文字修正後的完整本機回歸仍為 316 passed／18 skipped。
