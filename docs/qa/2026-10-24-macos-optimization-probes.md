# Mac：連線重用、批次輪詢與 Claude schema 重複提示研究

2026-10-24。Refs #39／#46，D-45。**優先驗證 HTTPS 連線重用與有界批次交付；Claude 去重複 schema 候選未證明總用量改善，這輪不採用。** 正式版仍0.9.12，4＋4常駐／64；本次沒有修改、停止、更新或部署正式Bridge／Worker，沒有新的release。

## 真實公開網路：連線重用

從原profile讀取既有HTTPS endpoint，僅GET `/health`，不帶Authorization、不使用裝置secret、不觸發模型。以相同Python `http.client.HTTPSConnection`／certifi TLS，一組每次新連線，另一組沿用連線；8組交錯A/B，另完整保留persistent首次建立連線的primer。不是與既有urllib Relay做正式同版前後比較。

| 實際公開HTTPS | 成功 | 中位秒 | 最大秒 | 8筆合計秒 | 確認同socket |
|---|---:|---:|---:|---:|---:|
| 每次新連線 | 8/8 | 0.9082 | 2.4380 | 8.7201 | 0/8 |
| 重用連線 | 8/8 | 0.3220 | 0.5865 | 2.9757 | 8/8 |

primer另為0.4179秒；persistent含首次建立連線共9筆／3.3936秒，沒有隱藏首次成本。17筆全HTTP200、device_online=true、will_close=false。中位下降約64.5%僅適用此健康檢查；這不是LLM API延遲或正式poll改善比例。沒有經過請求排隊／推論／結果回傳，也未測20秒idle後的連線存活。此probe為直接HTTPS連線；不能以忽略既有代理設定的方式移植到正式Relay。

## 不消耗模型的批次輪詢原型

[可重現原型](../../spikes/relay-batch/README.md)在RAM讀入現行Worker，僅對已核對的三段原文套候選；不改來源檔或正式服務。新agent opt-in `batch_size=1..8`，FIFO取待送工作，序列化後總量不超過6,100,000 bytes。舊agent仍收單筆request；新decoder接受舊Worker單筆。多筆已標dispatched的工作不重送，重啟仍503；容量64 inference＋8 controls保持原實作。

20項本機測試通過：7個新不變量與13個原Worker回歸；涵蓋FIFO／只交付一次、舊新版相容、空long-poll喚醒、bool／非整數／超範圍拒絕、真encoded-byte上限、批次重啟與遲到結果、重複ID拒絕，且storage.put會直接令測試失敗。新增只跑研究測試的CI，不部署或使用帳戶／模型。

下表使用**真Worker狀態機＋人為固定RTT**，先緩存同批合成請求，再逐次poll；`/agent/result`為無網路延遲的本機呼叫。沒有真HTTP／TLS／Cloudflare或CLI／模型負載，僅測分派，不是端到端。100ms各3對交錯，500ms只有1對，不混作中位樣本。

| 合成批次／設定RTT | 對數 | 單筆poll數→批次poll數 | dispatch p95中位毫秒：單筆→批次 |
|---|---:|---:|---:|
| 16／100ms | 3 | 16→2 | 1683.562→215.447 |
| 64／100ms | 3 | 64→8 | 6422.027→854.403 |
| 64／500ms | 1 | 64→8 | 30841.547→4060.939 |

所有合成工作都只交付一次並結束清空；RPC數少87.5%，但**不能用模擬p95宣稱正式55.6秒已縮短**。若第一筆到達時已有long-poll，首批可只有1筆；餘下才會成批，不能保證任何流量都有8倍收益。Python Relay尚未接入批次／連線池，這不是可部署正式方案。

## Claude 原生用量：去掉文字內重複schema

Claude Code2.1.306／claude-haiku-4-5-20251001，依原安裝read-only讀CLI路徑。直接呼叫原0.9.12 provider，不啟動第二個Bridge；獨立子程序與空cwd，訂閱登入沿用原生CLI。所有動態內容在stdin／RAM，原始事件與stderr不落檔，不修改CLI二進位／全域設定。這些直接CLI呼叫不寫正式API requests，也沒有偽造API receipt。

6對包含noul／choice／score各2對，再4對noul逐回合觀察；A/B順序交錯。baseline保留原prompt，candidate只去掉stdin裡重複的response_schema及要求純文字JSON的固定句，保留instructions、caller payload hash、原生--json-schema／StructuredOutput、restricted／tools空／MCP空／max-turns2、thinking／effort、typed validator及結果衍生。這不刪除caller內容，也不關閉推理。

| 10對真CLI比較 | 原版 | 文字schema去重候選 |
|---|---:|---:|
| 合成語意／原生StructuredOutput通過 | 10/10 | 10/10 |
| aggregate input | 15710 | 15051 |
| aggregate output | 5368 | 6161 |
| **total** | **21078** | **21212** |
| 單筆耗時中位秒 | 4.9609 | 5.3361 |

每對input少57–77，合計少4.19%；但output波動使total多0.64%、中位耗時也未改善。這個小樣本不證明候選造成output增加，亦不證明業務品質等價；足以否定「只看input較少即可上線」的判斷。因此**本輪不採用此修改**，維持正式Decisions原樣。三題型只是blue factual語意與合法機率驗證，不代表機率校準品質。

### 原生回合可觀測性

依 [官方CLI旗標](https://code.claude.com/docs/en/cli-reference)與 [官方stream事件](https://code.claude.com/docs/en/headless)，後8筆加4個並行baseline（共12筆）只增加--include-partial-messages這個輸出觀測旗標。記錄message_start／message_delta的固定usage數字、block種類及stop_reason，不記文字／thinking內容／工具參數。

12筆全部：1個model message，block含thinking＋StructuredOutput（部分另有text）、stop_reason=tool_use，stream完整usage加總與result aggregate四個input/output/cache欄位吻合；未觀察到api_retry事件，但native num_turns均2。**num_turns不是可直接代換的模型RPC數。** 普通assistant快照usage.output_tokens僅1–6，不能用它取代完整stream／result的306–1090等實際output；保持CLI aggregate完整計量，不能為省量把它錯減為答案數字長度。

4個並行baseline皆通過，input1546／1547／1546／1548、output715／472／306／463。**本輪24筆（14 baseline＋10 candidate）未重現3.5k input**，不推翻 [前輪](2026-10-24-macos-0912-staged-api.md)公開Claude Decisions的4/28異常，不能將其標成修好。要確認偶發多輪根因，後續需讓相同allowlist觀測跨正式API負載，而非記錄原文或根據num_turns猜測。

本輪共**24次真CLI、36,948 input／13,485 output**；全部cache read/write為0、語意／實際模型／原生格式通過，無Bridge推論重送。17次公開health與批次模擬模型呼叫都是0。沒有建立／輪替／撤銷client Key、沒有OpenRouter Key／帳單對照，也沒有更改個人登入。

## 採用前下一步與不變門檻

D-45將連線重用／有界批次排為優先候選，Claude文字schema去重暫不採用。正式移植需拆開poll與result連線，避免20秒long-poll阻塞回傳；保留既有proxy／TLS／不跟隨redirect，結果連線有界，失聯／未知交付不重送，跨舊新版可回復。補齊Python接收端、fault／deadline／容量、原生程序樹與同題公開A/B後才發布。批次會讓CLI真併發增加，不能把此前公開peak running10當作已驗64的資源預算。

仍沿用#39 cold/warm三輪及連續64、100對隔離、p95／38秒／good RPM／RSS等固定門檻；#46保持開啟。沒有因研究結果降低驗收、修改Windows發布或預設值。正式Mac保留0.9.12、4＋4／64、原URL／Key；這輪僅研究與文件，尚無正式poll／LLM速度改善承諾。

[完整allowlist metadata](../concurrency-evidence/macos-optimization-probes-2026-10-24.md)保留各次結果、首次連線成本及候選負面結果。新原型20項、原Relay13項、Bridge336 passed／18 skipped通過；文件／品牌／版本／secrets／whitespace另檢。私有terms本機未提供，由PR required CI使用secret核實。
