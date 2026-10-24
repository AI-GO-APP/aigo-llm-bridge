# Mac 0.9.12：4＋4 常駐、同題用量與公開同步負載

2026-10-24。Refs #39／#46。owner 授權測試；**112／112 真 API 推論成功，公開 64 筆單波正確性通過，38 秒門檻僅 38／64，完整 warm 效能放行尚未通過**。這是正式已安裝版本的測試收據，沒有修改或重發產品包。

## 固定條件與計量

- 正式 `0.9.12-mac.1`，來源 `fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12`，原 profile／Worker／URL。前次 [發布收據](2026-10-24-macos-chat-minimal-release.md) 的常駐2是當時配置；owner 後續已明確設定總數8：`codex-chat-minimal-v1` 4、`standard` 4，workers／pending64。standard 供 Decisions 與有 schema／tools／images 的 Chat 共用；Claude 仍 cold。
- 公開 HTTPS 三輪單筆（每輪 Codex／Claude 各 Chat／單題 noul），再各一波4、16、64同步請求，四類平均分配，兩把 RAM 臨時 Key 交替。單筆 Chat 是 o200k_base 估算500的固定合成輸入；burst Chat 是 `PONG` 短題，因此不把不同輸入長度當成版本前後比較。Decisions 同題 state 含不可信指令隔離資料。
- 每波以 thread barrier 同步起跑，收齊全部結果，沒有刪失敗、沒有推論重送；每次比對實際 model、語意、profile、完整 1/1 CLI receipt、回應／receipt／SQLite 的 input、output、cost。原生 CLI 內部模型步驟可多於1，1/1不代表只有一輪供應商推論。
- 序列測試每筆前與各波開始前確認8個 idle；每波結束並補池後才開始下一波。public 96筆／local補測16筆，**112次CLI invocation、148,415 input／16,831 output**。牌價等值 cost 合計 **0.299297 USD**，不是訂閱餘額或實際 OpenRouter 帳單。沒有真 OpenRouter receipt。

## 三輪同題（公開 HTTPS）

每列3筆，相同 payload hash、跨兩把測試 Key；p50是這3筆中位數，不能當長期SLA。

| 來源／API | input 三筆 | output 三筆 | p50／max 秒 | warm／cold |
|---|---|---|---:|---:|
| Codex LLM（500估算） | 506／506／506 | 6／6／6 | 4.8913／12.7113 | 3／0 |
| Codex Decisions | 2791／2791／2789 | 42／53／48 | 6.0324／7.2459 | 3／0 |
| Claude LLM（500估算） | 1061／1059／1062 | 117／112／110 | 5.8223／8.7044 | 0／3 |
| Claude Decisions | 1547／1547／1547 | 734／540／363 | 8.3450／12.9843 | 0／3 |

三輪序列 cache read/write均0，Codex 純 Chat 精簡效果重現。Claude Chat 仍有固定輸入與 output 開銷；Claude Decisions 的序列 input 穩定，但 output 波動明顯。在公開16／64 burst 中，同題 Decisions input 分別最高 **3543／3623**，因此前版收據的異常增加仍不能視為已解決。Bridge沒有重送，未擷取原生逐回合 usage／thinking／formatter 事件，不能指定內部原因；保持 StructuredOutput／thinking／formatter 不變。

## 同步批次與直連補測

| 路徑／同步數 | 成功 | p50 秒 | p95 秒 | max 秒 | 38秒內 | good RPM |
|---|---:|---:|---:|---:|---:|---:|
| 公開4 | 4/4 | 6.2458 | 10.4179 | 10.4179 | 4/4 | 23.028 |
| 公開16 | 16/16 | 11.5930 | 26.4049 | 26.4049 | 16/16 | 36.348 |
| 公開64 | 64/64 | 33.1998 | 55.6066 | 61.4533 | 38/64 | 62.464 |
| 本機直連16 | 16/16 | 4.3890 | 7.8651 | 7.8651 | 16/16 | 121.942 |

公開64的各類p95：Codex Chat56.7708、Codex Decisions57.4932、Claude Chat53.8603、Claude Decisions61.4533秒；各類16/16正確。全部API HTTP200、model／格式／成本與完整呼叫收據吻合。Decisions是合法且符合blue factual方向的 noul，不以此宣稱機率校準品質。

這是每個同步數各**一波**，沒有 cold arm、三輪／三連波64或100對真隔離 corpus。公開64的起跑數不能等同本機64同時推論：全公開測試取樣 `peak_running=10`，本機直連16才實際觀測到16。64批次Codex32筆全warm，而Claude32筆cold；這反映送達被攤開且池可補滿，不能當全64在同一瞬間有warm容量。

## 分段：主要尾端等待在 Runtime 外

`Runtime total_ms` 是本機受理後的驗證／排隊／provider／推論／清理總計；client HTTP時間扣此值包含 client排程／TLS／網路／Worker排隊／Relay分派及回傳，不是純模型時間，也不是純Relay時間。

| 批次 | client p95 秒 | Runtime p95 秒 | 逐筆 client−Runtime p95 秒 | 本機受理首末跨度秒 |
|---|---:|---:|---:|---:|
| 公開4 | 10.4179 | 4.989 | 5.7549 | 4.1282 |
| 公開16 | 26.4049 | 6.082 | 22.6480 | 16.5316 |
| 公開64 | 55.6066 | 6.179 | 52.5176 | 53.9492 |
| 直連16 | 7.8651 | 7.854 | 0.0134 | 0.0086 |

各欄分別取分位數，不能把兩欄p95直接相減；差值欄由每筆相減後再取p95。不同時段單波不能建立精確因果，cache亦不同：公開64 Codex Decisions總cache read8192、直連16總2048，均按收據保留，未把cache當零。

**推論**：增加本機workers或常駐數，未必改善這段公開等待。現行 [Relay](../../desktop_bridge/relay.py) 的單一 loop 每次同步 `/agent/poll` 僅取得一筆再取下一筆；[Worker](../../cloudflare/src/worker.js) 同樣回單筆。這是可驗證的結構性瓶頸候選，下一輪應量測 poll／dispatch／result 分段及批次交付候選，再做同版前後對照。這輪未修改／部署Worker，不能把全部52秒指定為poll造成，亦沒有將診斷當修補完成。

## 資源、清理與交付狀態

| 取樣（原服務與全部子孫） | 全公開輪 | 直連16 |
|---|---:|---:|
| peak tree RSS KiB | 2118016 | 3301296 |
| peak CPU%，100%=一logical core | 76.3 | 421.5 |
| peak descendants | 20 | 52 |
| peak tree fd | 2080 | 2800 |
| peak pool total（含active／idle等） | 18 | 24 |
| control health p95 秒 | 0.0020 | 0.0030 |
| sampling／health errors | 0／0 | 0／0 |

CPU 是 ps 程序生命期平均值的取樣峰值，非瞬時CPU；fd是proc_pidinfo描述資料bytes/8，短命程序可能漏採；sampler在原服務樹之外。兩段時長不同，不可用此表計算warm/cold RSS增幅。事前續測門檻為tree RSS≤8GiB、tree fd≤8192，未觸發；不是OS hard limit或一般產品資源建議。

直連補測腳本第一次在零筆serial樣本做max時出現ValueError，**在推論前結束，發出0筆API**；兩把臨時Key已撤銷，保留 [負面metadata](../concurrency-evidence/macos-0912-staged-preflight-2026-10-24.json)。修正空集合摘要後才開始計畫中的16筆，沒有重送任何推論。兩個成功段的測試Key也全數撤銷，共6把臨時Key均撤銷，原59筆Key rows／3把有效owner Key保留；每段設定與manifest hash比對未變。

測後服務回到accepting、idle8、兩profile各4、workers／pending64、running／queued／refill failures為0。正式版仍0.9.12；這次僅新增測試證據，不修改產品預設、不重發immutable Release，不改電源／登入或原裝置資料。兩議題仍開啟：#39的完整cold/warm與真正本機64／持續資源門檻未驗；#46的Claude／其餘模式額外用量仍待追蹤。

完整固定allowlist metadata：[公開96筆](../concurrency-evidence/macos-0912-staged-public-2026-10-24.json)、[直連16筆](../concurrency-evidence/macos-0912-staged-loopback-2026-10-24.json)。原始request／response／事件／stderr／完整Key皆不保存。
