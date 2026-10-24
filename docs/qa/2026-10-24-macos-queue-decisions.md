# Mac 排隊與 Decisions 階段 0–2：候選證據

日期 2026-10-24（Asia/Taipei），候選 0.9.7-mac.1，基線來源 main 5d5e406。範圍為 [#36](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/36)，門檻固定於 [效能計畫](../PERFORMANCE-PLAN.md)；warm CLI 池另列 #39。

本文件只記實際證據。Source 實作、單元／HTTP 回歸、deterministic 基準、真訂閱、HTTPS、Release 與正式安裝為不同層。未通過的欄位不能用相鄰層證明。

## 狀態

| 層次 | 本輪證據 |
|---|---|
| Source | 已實作可取消 FIFO、受理預算、容量設定、numeric timings、固定 Decisions 驗證；原始碼候選 |
| 回歸／維護 | 最終本機 Bridge＋tools 316 passed／18 skipped；Worker 13 passed；version／branding／product docs／secret scan 通過 |
| 合成基準 | 完整矩陣＋最終 64 配置＋三波持續負載，共 7,296/7,296 正確；HTTP／真 schema 子程序／替身 runner，未啟動訂閱 CLI |
| 真訂閱 3 輪混合 64 | 初版兩組已測，未達放行；D-36–38 修補後另驗，不將合成數字當訂閱收益 |
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

## 發布前相依修補

Mac 與 Windows source CI 均通過後，Windows installer 的既有 OSV 閘門仍擋住 undici 7.29.1。維持 Wrangler 4.152.0，以 npm override 精確鎖定同一 major 的 undici 7.30.1，重新產生 lockfile；這是上游三份公告共同的修補版本（[EventSource memory](https://github.com/nodejs/undici/security/advisories/GHSA-4qv8-2p9j-2685)、[SRI](https://github.com/nodejs/undici/security/advisories/GHSA-f72v-6w45-q472)、[content-encoding](https://github.com/nodejs/undici/security/advisories/GHSA-xjj6-f33q-929c)）。未略過或放寬掃描。`audit_dependencies.py` 120 個鎖定版本查詢零公告，npm audit 零漏洞。此修補不發布 Windows 套件。

掃描通過後的 Windows installer 回歸暴露一處測試清理仍呼叫已移除的 `runtime.pool.shutdown()`；排他 socket 斷言本身通過。改用正式 `runtime.stop()` 清理 queue／monitor／workers，保留全部 Winsock 測試與安全斷言，不以 skip 避開。

## 近 3 MB 滿額排隊

`tools/benchmark_queue_memory.py` 以獨立合成 profile、1 running＋63 queued，連續三輪各 64 筆 2,999,080-byte JSON；第 65 筆皆在推論前回 429。每輪 63 個 queued spec 的 weak references 均釋放，calls_started=0，取消耗時 25.1／26.0／59.7 ms；停止後 queue／owned workers 均零。RSS 取樣峰值約 278／323／339 MiB；Python／macOS allocator 保留已釋放頁面，drain 後 RSS 不立即回落，不能聲稱清空後回到初始 RSS。內容未落盤，僅 aggregate metadata。

## 真訂閱測試器校準

首次 Haiku 4.5 混合 64 皆 HTTP 200、64 筆完整收據，但測試器誤把 noul 合法機率限定為恆等 0.9，誤列 10 筆不符（54/64）。此輪保留為校準紀錄，未列入效能放行；修正為 API 的固定欄位／finite 0–1 格式檢查，另由回歸驗 bool／非有限值／多餘欄位必須拒絕。不重送原 request ID、不挑最佳輪，也不以不同答案值宣稱機率校準相同。

## 第一組真訂閱：未達效能門檻

原安裝 0.9.5-mac.1 runtime（與計畫 main 5d5e406 僅版本常數不同）對候選 ee11b13，Haiku 4.5、各三輪 32 Chat＋32 單題 Decisions；各輪 64/64 正確、模型／格式／成本與單次呼叫收據一致。這組保留原始 numeric-directive 題目（要求模型指定 noul=0.9，屬自指指令而非標準判真題），兩版輸入相同，無重試。[完整 metadata](../concurrency-evidence/macos-live-numeric-2026-10-24.json)。

| 三輪中位數 | baseline | ee11b13 | 變化 |
|---|---|---|---|
| Decisions p95 | 45.0514 s | 43.5857 s | -3.25%（未達 -20%） |
| Chat p95 | 6.8093 s | 8.2792 s | +21.59%（超過 +10%） |
| good RPM | 69.836 | 76.301 | +9.26% |
| 38 秒正確完成數 | 61/64 | 61/64 | 相同 |

因此此來源不放行正式發布。分段計時顯示 burst 重複啟動 auth status 增加 provider_setup；依 D-36 只合併重疊的唯讀 metadata 查詢，並使該查詢可取消、程序群組清理後才回錯，不增加 warm inference CLI。baseline 程序樹 RSS 取樣 9,875,280 KiB、候選 12,181,536 KiB；baseline sampler 從第一輪後才開始，明列較保守的不完整覆蓋，不能冒稱完整首輪峰值。CPU 是 ps 生命期平均取樣而非瞬時峰值。

後續正式固定負載在重跑前明定採產品既有 blue-object factual probe，兩版各三輪、原數值門檻不變。此改動避免把 noul 判真題與改寫機率協定的指令混為一談；numeric-directive 的負面結果完整保留，不與 factual 混算、不外推任意推理長度的收益。近 3 MB 三輪 RAM 收據見 [JSON](../concurrency-evidence/macos-queue-memory-2026-10-24.json)。

## Factual 初版與發布前修補

完整 [第一組 factual metadata](../concurrency-evidence/macos-live-factual-initial-2026-10-24.json) 保留 baseline 三輪（46／64、64／64、64／64）與 a265fef 三輪（64／64、63／64、64／64）。baseline 首輪 18 筆自有合法 schema 超過隔離預算，回 400 unsupported_parameter；初始工具在失敗後提早結束，後續只補完原定另外兩輪，未重送那 18 筆，不剔除首輪。效能計畫明確修訂為 baseline 失敗計入統計、candidate 仍須每輪全對；修補舊缺陷不以舊版先全過為前提。

D-36 已使 factual Decisions p95 中位數 17.0286→12.5876 s（-26.08%），Chat 9.1072→6.8898 s（-24.35%），good RPM 215.565→222.993（+3.45%）。但一筆模型格式錯誤回 502，且程序樹 RSS 9,268,592→12,225,440 KiB（+31.90%，超過 +25%），故仍未放行。不得用延遲改善掩蓋正確性／記憶體門檻。

D-37 限定自有 Decisions 使用 Claude CLI 原生固定結構輸出，依 [官方 structured output](https://code.claude.com/docs/en/headless#Get-structured-output) 與本機 CLI help 核對，單筆真訂閱成功，7.862 s；未列入正式三輪。D-38 以 40 ms 冷啟動間距緩和瞬間程序負載；保持既有 64/64、固定期限與不重試。新增 canary 回歸證明 caller state／instructions／criteria 名稱／外部 schema 不進 argv、原生 structured_output 必須存在；取消／期限／generation 在等候後仍核對。兩項修補後必須重驗，未先宣稱通過。

943b789 的原生結構＋40 ms 首版三輪為 47／49／50 正確，CLI provider_error 17／15／14；不是放行證據。[metadata](../concurrency-evidence/macos-live-native40-2026-10-24.json)。RSS 降至 5,536,960 KiB，但 Chat p95 約 11 秒，未通過速度／正確性。調為原生結構 CLI turn 上限 2，容納其結構終結步驟；每題仍僅一次 Bridge CLI 呼叫，無本機工具或 Bridge 重送，usage／cost 依 CLI 合計。另將啟動間距改為 20 ms，須重新核實。單筆協定 probe 的 CLI result 可回 num_turns=2，metadata 未含原文；不把 CLI turn 計數冒稱實際供應商 RPC 次數。

完整本機回歸於 943b789 為 403 passed／23 skipped；後續 native turn／pacer 參數的針對性回歸 22 passed。格式缺失可拒絕，但已核對的模型用量／成本須先保存；另有回歸確認 502 的 calls_started=calls_completed=1、billing_complete=1、cost>0。benchmark 成本改從 receipt 加總，包含已知成本的失敗，不把失敗當作零費用。

01e8596 的 native turn=2、所有請求共用 20 ms 間距已達三輪 192/192 正確、收據完整，RSS 6,190,480 KiB（低於 baseline）；但 Chat p95 中位數 11.2189 s、Decisions 15.0653 s，仍未放行。[全部 metadata](../concurrency-evidence/macos-live-native2-allpaced-2026-10-24.json)。因此將啟動節流限於因固定 schema 快速路徑而集中啟動的 Claude Decisions；一般 Chat 與 Codex 沿用原啟動方式，沒有更改 queue FIFO 或 64/64 容量。CLI 原生結構模式會增加部分輸入／終結步驟用量，本組每輪已知 cost 約 0.202–0.206 USD 等值，較 baseline 後兩輪約 0.144 高；這是 CLI token 的公開牌價估值，不是另收 API 費用，也不隱藏於 calls_completed=1（其單位為 CLI 呼叫）。調整後另驗，保留負面結果。
