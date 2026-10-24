# Mac 效能階段 0–2

2026-10-24 owner 授權實作 [#36](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/36)。warm CLI 池拆至 [#39](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/39)，本批不啟用任何常駐 CLI／validator 池。已發布 Mac 0.9.7-mac.1；[效能 QA](qa/2026-10-24-macos-queue-decisions.md)與[發布收據](qa/2026-10-24-macos-queue-release.md)分層記錄。

## 交付契約

1. 階段 0：固定 allowlist 分段毫秒 metadata，monotonic 計時；只存數字，不存 body、答案、schema、事件、stderr、任意 trace 或憑證。未觀測為 null，spawn 不等於 ready。子階段有重疊，不能相加當總時間；詳見 [SCHEMA](SCHEMA.md)。
2. 階段 1：驗證前保留名額；驗證＋排隊＋執行合計至多 64，執行上限 1–64。有效工作依入隊順序 FIFO；queued 取消／撤 Key／逾時移除 spec 並釋放名額，只完成一次。新 profile 64/64；舊明確 workers 缺 pending 者保留原受理容量，明確改設定才加大排隊。
3. 階段 2：僅自有 noul/probabilities 固定型別驗證，保留 duplicate key、bool、有限值、欄位／長度、0–1、總和容差、順序／tie／confidence 語意。解析上限 1 MB／深度 4。外部 schema 不走快速路徑，維持四個一次性隔離程序及原平台預算。

同步本機受理時固定 min(90 秒、timeout_s、X-Bridge-Deadline)；jobs 使用 min(timeout_s、外部 deadline)，都包含驗證與排隊。schema 等名額最多 30 秒、執行最多 3 秒，且都不得超過剩餘期限。CLI stdin 寫入也可取消／逾時；程序清理完成才標 terminated。公開 Worker 斷線沒有完整取消傳播，只依原 deadline 限制，不自動重送。

## 正確性放行門檻

- 32 running＋32 queued，第 65 筆 429；Chat、Decisions、兩 provider 共用容量。
- queued 取消／撤 Key／逾時於 1 秒內完成並釋放，runner 零呼叫、calls_started=0、無未知成本；新工作不等前方 CLI 即可受理。期限誤差不超過 1 秒；子程序清理另允許 5 秒，未清理不宣稱 terminated。
- FIFO、去重／衝突、pause／drain／stop、設定原子性、舊 profile／DB／版本回復通過，既有已知／未知計費語意不變。
- 滿載本機控制 GET p95 <1 秒；3 MB body 滿額時記憶體有界，清空後無 queued spec 或自有程序殘留。
- 固定／隨機邊界 corpus 與 Draft202012Validator 結構有效性一致，語意 golden tests 全過；Decisions 零 schema 子程序。外部惡意 regex 仍隔離且主程序不被卡住。

## 效能比較與門檻

同機、同 CLI／模型／輸入／輸出限制，baseline／candidate 不同時執行；先 deterministic runner＋真 schema 子程序，再真訂閱驗選定配置，不互相代認。

| 維度 | 固定設定 |
|---|---|
| 執行數 | 32、48、64；pending=64 |
| 負載 | Chat-only、Decisions-only、32 Chat＋32 Decisions |
| 題數 | Decisions 每筆 1 題及 3 題，逐題串行 |
| 輪次 | 每配置 3 輪 64 burst；另測 3 波連續 64 |
| 報告 | 每輪／中位數、正確率、good RPM、p50/p95/max、38 秒達成率、CPU 尺度、程序樹 RSS、fd／程序峰值 |

不啟動訂閱的工具：

```sh
python tools/benchmark_queue.py --source /path/to/baseline --rounds 3 --output /tmp/baseline.json
python tools/benchmark_queue.py --rounds 3 --output /tmp/candidate.json
python tools/benchmark_queue.py --waves 3 --rounds 3 --output /tmp/candidate-sustained.json
python tools/benchmark_queue_memory.py --output /tmp/queue-memory.json
```

真訂閱比較使用 `python tools/benchmark_live_queue.py --apply --label baseline --rounds 3 --output /tmp/live-baseline.json`，排空並切換候選後以相同參數、`--label candidate` 另跑；`--public --rounds 1` 另驗真 HTTPS。正式固定負載採產品既有 blue-object factual probe，baseline／candidate 必須各三輪，不能混用不同題目。另保留 `--workload numeric-directive` 的自指機率指令壓力結果，不與 factual 合併中位數。此工具會消耗本人訂閱，以 RAM 臨時 Key、固定合成內容、唯一 request ID 檢查回應模型、格式及成本／呼叫收據，結束撤銷 Key，不自動重試。Decisions 僅檢查其合法機率格式，不要求模型機率恆等於提示內數字或宣稱校準品質。效能改善限於對應負載，不外推至任意推理長度。

工具只存 aggregate metadata／暫時 SQLite metadata 與 key hash，結束撤銷測試 Key 並刪暫時 profile；ps CPU 是程序生命期平均的取樣峰值（100%=一個 logical core），不是瞬時峰值，sampler 自己也計入 descendant 峰值。須另以真訂閱測 CLI 程序樹。

- deterministic 每輪 64/64 正確且 model／receipt／cost／call counts 一致。同 workers 混合 Decisions p95 中位數至少下降 30%，Chat p95 不增加超過 10%，good RPM 不下降超過 5%。
- 真訂閱 baseline／candidate 各至少 3 輪混合 64（32 Chat＋32 單題 Decisions）；**candidate 每輪必須 64/64 正確、完整收據與成本一致**。baseline 的原有失敗也須保留並計入 good RPM／38 秒達成率，不要求舊缺陷先通過才允許修補；p95 以該類全部請求計算，失敗不刪除。Decisions p95 中位數至少下降 20%，Chat p95 不增加超過 10%，good RPM 不下降超過 5%，38 秒達成率不下降。不用重試補成功。此基線規則於發現舊版固定 schema 在滿載會回 400 後明確修訂；未降低候選正確性或數值門檻。
- 同配置 peak tree RSS 不增加超過 25%，完整報告錯誤／timeout／限流與 max，不挑最佳輪。
- 32／48 只有 good RPM 提升至少 10%、p95 不差超過 5%、38 秒達成率不下降且安全門檻全過才替換 Mac 新預設，否則維持 64；Windows 預設不依 Mac 結果變更。
- 真 HTTPS 64 為獨立閘門；Cloudflare 配額／1101 阻擋時記未驗，不買方案、不以本機或 401 代替。

## 發布與回復

同 PR 同步需求、API、資料、架構、安全、D 決策及驗收。跑 Bridge／tools／Worker tests、version、branding、product docs、terms；缺本機私有 terms 清單由 CI 核實。前端僅校正受理容量文案，不新增功能；六頁、深淺色／窄版及 Windows 適配卡另做 renderer 回歸。不發布 Windows、不自動部署 Worker。Mac 依 [MACOS-RELEASE](MACOS-RELEASE.md) 分層驗收；未達實機門檻不改正式預設或宣稱 release。

回復先 pause/drain，恢復前一 source manifest／依賴，保留新 DB／nullable metadata，容量可明確設回 64/64。profile、URL、device ID、KEY、登入與 Worker 不變。

D-49／R-29的0.9.16是owner另行明確授權的Mac4＋4／32／32與零推論簡易驗收，不以此替換本文件32／48／64一般效能比較門檻、宣稱32負載通過或改其他profile／Windows預設。[本輪收據](qa/2026-10-24-macos-32-operator-release.md)。
