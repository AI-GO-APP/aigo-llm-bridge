# Mac Codex 上下文調查與精簡（issue 46）

2026-10-24；產品 Local Token Buffet Bridge。使用者在分析完成後明確「同意開工」，本輪實作 D-41 goals／技能精簡。已合併 [PR #47](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/47)，發布 [0.9.10-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.10-mac.1)，匿名下載驗證並更新原 Mac。現在接單、Codex 常駐 2／workers=pending=64、idle=2。Windows 原生訂閱與完整 issue 39 放行不由本輪替代。

## 原問題與本機核對

[issue 46](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/46) 的 Cloud 東京測速為獨立測試，不與 Bridge 自己的樣本混算。SQLite allowlist metadata 核對其 7 筆成功請求，均 calls_started/completed=1/1，未見 Bridge 重送；三筆 warm Decisions 均 warm=1/cold=0，仍約 4340 輸入。Chat 三筆為 4188–4192；當時尚無 warm/cold 欄位，不補造。其部署時間落在 0.9.8，Decisions 落在 0.9.9，屬部署時間推論，非逐列 version/SHA 證明。

503 UUID `ad2c2243-38fd-492d-a88f-6b671e298420` 在全 Key 請求 metadata 均不存在。當時原機升級與隨後 off/on 啟停重疊；pause 的受理前拒絕／relay offline 等都可能造成 503 與無收據，未保存 error_type 不能鎖定根因，不能認定零成本或重送。原 LaunchAgent stdout/stderr 為 /dev/null，資料目錄沒有可回溯原始 error body 的 log；僅有 SQLite metadata。新增除錯不以落盤原文補洞。

warm 成功批次的 CLI turn 約 3984–4164 ms、provider setup 約 88–131 ms，queue=0；常駐省初始化，不省逐題 harness。codex_usage 直接映射 inputTokens／outputTokens，cache／reasoning 為子集，沒有加回總 token。多題 Decisions 仍每題重付 state／協定與 harness。

## Mac 受控上游封包

真 Mac arm64、Codex 0.163.0-alpha.11；隔離 HOME／CODEX_HOME／XDG／空 cwd，mock Responses provider 僅綁 loopback，不使用訂閱或 owner 憑證。封包只在 RAM 分類，保存長度、hash、欄位與已知 marker boolean；無原文／headers／auth.json。mock 回報零 usage，不作計費證明。o200k_base 為近似估算，JSON 序列化及 native template 差異不能直接等同 provider input tokens。

| 診斷設定 | additional_tools JSON 估算 | 技能區塊估算 | 全 input JSON 估算 |
|---|---:|---:|---:|
| 原 Bridge flags | 3649 | 492 | 4885 |
| goals=false | 2985 | 494 | 4237 |
| goals=false、技能 budget=1 | 2985 | 106 | 3836 |
| goals=false、明確停用列出的全技能 | 2985 | 0 | 3724 |

原先分析使用一次 metadata probe＋新程序，確認有效語法；正式候選改為同一 app-server，claim 前 skills/list，再以 thread/start.config 的 typed dotted `skills.config` 套用。候選實際 mock 路徑完成一個 thread／一個 turn，skills/list=1，goal 三個 marker=false、skills_instructions／SKILL.md=false，input JSON 近似 3719 tokens；無額外 metadata 程序，ephemeral path=None、無 rollout 檔案。

`additional_tools` 是 input 中獨立 developer item，不是頂層 tools。仍含 exec／wait／詢問使用者及內嵌 apply_patch／MCP resource 等定義；保留權限、協作模式、環境。停用執行或 dynamicTools=[] 不代表這些 token 消失，看到定義也不代表曾執行工具。Bridge 自加指令僅 105＋57 字元，估算約 33 tokens；Decisions 固定 SYSTEM 505 字元約 88，單題序列化 145 字元約 37，原生 outputSchema 包裝約 58，仍不足以單獨解釋 4.2k。

官方依據：[config reference](https://learn.chatgpt.com/docs/config-file/config-reference)、[app-server](https://learn.chatgpt.com/docs/app-server)。goals 與 per-path skills.config 可覆寫；skills/config/write 會寫設定，本輪不用。unified_exec 的使用者 opt-out 不能保證移除一切內建宣告，不改管理員 requirements；尚未驗得一般化零內建工具旗標，不呼叫私有訂閱 endpoint。

## 實作與驗收門檻

- 冷／warm 同一 call_codex 路徑，每題 claim 前 skills/list(forceReload=true)，當前空 cwd、無 caller 內容、無 thread／turn。pool 待命仍只 initialize／initialized。
- 清單必須單一正確 cwd、errors=[]、最多 512 筆，每筆 enabled bool、絕對 path 長度 1–4096 且無 NUL。typed config 停用全列出路徑；不寫個人 config、不讀取技能原文、不新增持久 cache。
- 清單異常回 503 codex_context_unavailable，不回退為帶技能推論；RPC／取消／期限錯誤沿用既有分類。查詢一次且計入 provider_setup_ms／原 deadline，失敗關閉自有程序，thread=turn=0；不重送。
- 保留個人登入／設定、原 profile／KEY／Worker、常駐 2／workers=pending=64、一程序一題、ephemeral／sandbox／工具事件拒絕、原 schema／history／模型核對與完整計量。
- 必須通過維護與 PR CI，再公開 Mac source release、匿名四附件校驗與 ZIP 實際安裝／原 profile 更新。真 API 用相同短 Chat／單題 Decisions、模型、常駐值，各版兩組，併發 1、無重試、臨時 Key finally 撤銷。cache 必須列出；小樣本不推論 p95、SLA 或純上下文延遲收益。

## 本機候選驗證

本機完整 `desktop_bridge/tests tools/tests packaging/windows/tests`：469 passed、23 skipped；Worker relay：13 passed。Mac 原生 Cocoa 六頁／五步／深淺／窄版／容量卡等共 64 個畫面，剪貼簿、真 NSSavePanel 取消／保存、CSV、關窗留服務均通過。branding、product docs、version 與 diff 檢查通過。`lint_terms --require` 本機缺 private 清單，仍須由有 repo secret 的 CI 驗證，不將此項當作本機已通過。新增測試覆蓋清單異常、無額外本機檔案、個人 config 保留、錯 cwd／設定寫入 RPC 拒絕、一次性查詢、取消／逾時及 thread/turn=0。

完整發布、逐筆 usage／耗時／cache 與保留檢查已收錄 [數字證據](../concurrency-evidence/macos-0910-codex-context-2026-10-24.md)。本機 gitignored 診斷不作唯一交接來源。

新版前的固定短題公開基線（0.9.9-mac.1、resident=2、gpt-6.1-sol）：Chat 4191／4193 input，中位 5.0285 秒；Decisions 4333／4335 input，中位 6.0185 秒。四筆均 warm=1、cold=0、完整 1/1，兩筆 cache=3072、另兩筆=0。這是本輪獨立基線，題目與 Cloud issue 的原批次不同，不能混算。


## 公開發布與原安裝

來源 `26ab468b157747f1de6ea5dc3e934874b2f6bedf`，ZIP SHA256 `122b6e1f1fd2fcee433c1521f71febb56dd59367ad14e50d13ea6a56d5689f8c`。[Mac 發布 workflow](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40067596369) 與 PR 核心／私有 terms、Mac source／native／ZIP、Windows source／installer 更新均全綠。四附件匿名下載、manifest clean／commit／hash、所有 runtime Python 與測速工具來源一致；公開 ZIP 實際安裝、全機互斥、停止驗收通過。

原 0.9.9 profile 升至 0.9.10，同一臨時 Key 跨升級驗 models、Chat／成本、去重、JSON schema、工具提案、預期 unsupported_parameter 400 與交接，全部通過。工具仍由 caller 執行。原設定、49 筆升級前 Key rows（含本輪已撤銷的基線測試 Key）、3 把原有效 owner Key、個人 Codex config hash 全保留；三把本輪臨時 Key 均撤銷。Worker／URL／裝置／登入未重建，無 Cloud 部署／Windows 發布／電源鎖定變更。

實際常駐 2 時 stop=1.1648 秒，觀測到的 3 個自有程序與 2 個空 cwd 均清空；重啟回 accepting=true、running=queued=0、idle=2、2/64/64。上一版 0.9.9 manifest／app 與同一 DB 保留供回復。這是小量生命週期驗收，不替代 issue 39 全量尖峰／資源門檻。

## 真實輸入與時間前後比較

同一固定短題、gpt-6.1-sol、公開 HTTPS、每版每 API 各兩筆、resident=2、併發 1、無推論重試。8/8 成功、warm=1/cold=0、receipt 完整 1/1，模型／格式／成本一致。不是 off/on，也不與 Cloud 東京批次混算。

| API | 原 input tokens | 新 input tokens | 中位 input 減少 | 原時間中位 | 新時間中位 |
|---|---|---|---:|---:|---:|
| LLM Chat | 4191 / 4193 | 3121 / 3119 | 25.57% | 5.0285s | 5.4937s |
| 單題 Decisions | 4333 / 4335 | 3263 / 3259 | 24.76% | 6.0185s | 6.0245s |

輸入中位數分別下降 1072／1073 tokens；**這組延遲未見改善**，Chat 中位慢 9.25%、Decisions 約持平。樣本少、前後分時、網路／CLI turn／reasoning 與 cache 不同，不能推論純上下文因果、p95 或 SLA。Chat cache 原 0/3072、新 0/2432；Decisions 原 3072/0、新 0/0。cache 是 input 的子集，不再加總；不能用 gross input 降幅宣稱訂閱扣額必定同比下降。

診斷工具 0.9.10 的 cache／reasoning 欄位讀取 compact receipt 而得到 null；該 receipt 只有總 tokens／cost，程式註解所稱完整 subsets 不成立。**本輪已按逐筆 UUID 從本機 SQLite allowlist metadata 補核對上述 cache／reasoning**，不是將 null 當零；核心 API、計量與時間沒有重跑／改值。工具後續應從已查詢的本機 request row 補欄位，修補前不能只依該工具的 null 判定無 cache。此限制不影響本輪實際輸入降幅或正式 runtime。

本輪基線 4 次＋升級 3 次＋新版對照 4 次，共 11 次完整計量 CLI 呼叫，39,451 input／218 output tokens，牌價等值 USD 0.0601668；另有預期 400、零 CLI。沒有為改善數字增加樣本或重試失敗推論。原始內容、events、stderr、憑證均未保存。

## 剩餘範圍

本輪完成 goals／技能精簡並正式上線，仍有約 3.1k Chat 固定輸入；Codex 其餘內建工具／權限／環境尚未移除。issue 46 保持追蹤後續官方純推論工具集合或上游變更；Decisions 多題合併另訂隔離／schema／計量契約。外部使用者的獨立時間基準由 owner 後續發動，本輪未代替其測試。
