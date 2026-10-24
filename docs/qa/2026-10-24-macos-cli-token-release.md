# Mac 0.9.11 CLI token 精簡與發布驗收

日期：2026-10-24。Refs #46；完整 warm 放行門檻仍追蹤 issue 39。

## 狀態

已合併、公開發布、匿名下載／實際 ZIP 安裝，並更新 owner 原 profile。正式版本 0.9.11-mac.1，常駐 2／workers 64／pending 64；原入口、裝置、owner Key 與設定保留。後續 schema／thinking 實驗只在隔離子程序，未混入此 immutable runtime。

## 變更與門檻

依 D-42 採用 PR 49 的兩項候選：Codex 子程序 code_mode table disabled＋排除 functions／clock；Claude 僅自有 generated_schema Decisions 的固定提示允許 StructuredOutput 直接格式化。保留 Chat／外部 schema、本機 tools 空、strict MCP 空、訂閱登入、單次 CLI、每題隔離、取消／期限及完整 CLI usage。不存在推論重試、managed requirements 變更、--bare 或憑證轉送。

必須通過完整共用／工具回歸、Worker tests、版本／品牌／產品文件／CI 檢查，原生 Cocoa 六頁／五步深淺與窄版、剪貼簿／CSV／生命週期、實際公開 ZIP 安裝與單機互斥／清理。固定合成真推論須驗兩 provider 的 noul／choice／score 與指令攻擊、模型一致、typed output／計量；正式更新後用公開 HTTPS 短 Chat／Decisions 同題比較。所有測試只留數值／布林 metadata，臨時 Key RAM-only 並撤銷。Windows 不在本次發布範圍。

## 先前研究基線

PR 49 的 Codex 每 arm 一題，Chat input 3120→2630、Decisions 3257→2769；Claude formatter 單題 input 3666→1529。樣本極小、CLI cold 與公開 warm 不混用，這些不是正式 0.9.11 成效。原始研究及限制見 [續測](2026-10-24-macos-cli-context-followup.md)。

## 後續研究

先部署本版，再以 credential-free mock 拆解仍有的工具／提醒與重複 schema；只有維持訂閱、隔離與完整格式驗證的候選才做小量真實測試。新候選不自動混入已發布不可覆寫產物。issue 46 維持開啟。

## 本機已通過

- 共用核心、工具及 Windows packaging 回歸：472 passed／23 skipped；不等同 Windows 原生訂閱驗收。
- Worker relay 13 passed；產品文件、品牌、版本一致、diff whitespace 均通過。私有 terms 清單本機不可用，由 CI secret 執行 required gate。
- Cocoa 真實 renderer：64 個畫面，六頁／五步／容量／平台卡、深淺與 1200／480 寬；原生剪貼簿、CSV save/cancel、關窗後服務、容量控制全部通過。
- 4 次原生 credential-free loopback：Codex Chat／Decisions 都是一個 initialize、一個 skills/list、一個 thread/start／turn/start，無 auth header、goal／skill／內層 apply_patch／MCP resource 宣告，ephemeral 且清理完成；Claude Chat tools 空、Decisions 唯一 StructuredOutput，無 session jsonl、子程序清理完成。
- 公開基線第一次模型清單 GET 非 JSON 503，未發動推論；保留失敗收據。另行唯讀診斷中 Python 預設 User-Agent 收到非 JSON 403，產品驗收 UA 可收到認證 JSON；沒有重送推論或降級 TLS。第二組正式基線另存，不覆寫失敗。

## 合併與發布

- 實作 [PR #50](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/50)，source SHA `f9b481047485a9be8c0351a3b44139064e021c86`。
- PR CI：core [40072008528](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40072008528)、Mac [40072008522](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40072008522)、Windows [40072008509](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40072008509)、installer [40072008552](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40072008552) 全數成功。
- [Mac source Release](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.11-mac.1)，發布 workflow [40072496562 attempt 2](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40072496562/attempts/2)。匿名下載四附件，manifest／clean commit／self-test／size／SHA256 全通過；核心與 opt-in 工具 bytes 對應 reviewed source，包內無 owner 設定。
- 發布 workflow attempt 1 核心 311/18 通過，但 native key_cleared_on_close=false，publish skipped。程式 close 事件排程清除 Key、probe 卻立即讀欄位；隔離 WKWebView 重現 immediate=false、事件執行後 true。保留負面紀錄，只重跑失敗 job，未改來源或放寬門檻；attempt 2 成功後才發布。後續應讓 probe 等待 bounded close event，而非以立即讀值判定。
- ZIP SHA256 `683107fed3eb457c9a9cf69c8697a47ea8a609a2044de88cbdec88ca9b626c02`。公開 ZIP 實際安裝／啟停／單機互斥通過；同一臨時 Key 跨原 profile 更新驗 models／Chat／cost／dedupe／外部 JSON schema／caller tool proposal／unsupported parameter／handoff，無 Bridge 推論重送。
- 原 profile 乾淨停止 0.6976 秒；3 個自有程序及 2 個空 cwd 全清理；重啟常駐 idle 2。先前 56 筆 Key rows 全保留，3 個有效 owner Key，新測試 Key 全撤銷，個人 config 不變，0.9.10 rollback app／manifest 保留，資料庫沿用。

## 真實型別與隔離

兩 provider 各 noul／choice／score，6 次 native subscription CLI 單次推論、串行無重送，state 含工具指令注入。全部 typed output、模型一致、結束與 CLI 計量通過；Claude 每題僅一個 assistant response、只有 StructuredOutput、無 preliminary text，CLI num_turns=2 包含 terminal 格式化。input：Codex 2792／2818／2801，Claude 1553／1620／1601；Claude output 822／517／2095，不能宣稱輸出／推理成本已最小化。這些是格式與工具隔離測試，不是概率品質／校準基準。

## 原機公開 HTTPS 同題比較

兩版本相同模型／請求 bytes、2/64/64、每組 2 題、串行且每題新 UUID；Codex 真 warm、Claude cold，16/16 receipt calls_started=calls_completed=1、billing complete、成本相符；兩個臨時 Key 均撤銷。下表 input 與秒數取中位數，含 provider 原生內部步驟完整計量，不拿 cache 折價當 input 減少。

| Model／API | 0.9.10 input | 0.9.11 input | input 減少 | 0.9.10 秒 | 0.9.11 秒 |
|---|---:|---:|---:|---:|---:|
| openai/gpt-6.1-sol／chat | 3122 | 2631 | 15.73% | 5.7978 | 5.4135 |
| openai/gpt-6.1-sol／decisions | 3259 | 2774 | 14.88% | 5.7949 | 9.0641 |
| anthropic/claude-haiku-4.5／chat | 563 | 563 | 0.0% | 2.7142 | 3.2176 |
| anthropic/claude-haiku-4.5／decisions | 2488 | 1528.5 | 38.57% | 5.8715 | 5.4323 |

Claude 原版 Decisions 一題已直接格式化（1485 input），另一題 3491；新提示不能保證所有模型永遠只有一個原生推論步驟。小樣本、不同時段與 cache／output 差異無法建立延遲因果、p95／吞吐或長期節省保證。cache／reasoning 改讀同 key＋UUID 本機 metadata，本輪不再把 compact receipt 的省略當零。完整數據與 UUID 見 [metadata](../concurrency-evidence/macos-0911-cli-token-2026-10-24.md)。

## 上線後續測

- 重複 schema 候選：僅對 Claude generated_schema 的 stdin 移除已透過原生 --json-schema 提供的副本；保留所有 state／instructions／criteria 與既有 native schema、formatter prompt、typed validator、限制及完整 usage。4 次 credential-free mock（Chat 對照兩次、Decisions 兩次）和三題型小量真 CLI 結果見 metadata。尚未整合正式程式／發布。
- MAX_THINKING_TOKENS=0 候選：只覆寫隔離 Haiku 4.5 推論子程序環境，訂閱登入沿用 native CLI、owner 設定與正式服務不變；三題型語意簡測及用量見 metadata。這會改變推理行為，簡單藍色合成題不能證明實務決策品質／概率校準不變，不自動採為正式預設。
- Codex 仍有 exec／wait／ask 外層宣告；mock 工具 JSON o200k 估算 2426，不等於 provider 計費，也不宣稱零工具上下文。既有 exec 替代與其他旗標試驗未找到保持既有契約的零工具方式。
- --bare 不讀訂閱 OAuth／Keychain，維持排除；不讀憑證、不私接 provider endpoint、不共用跨 caller thread、不移除原始 caller 內容、不省略或重送失敗計量。issue 46 與完整 warm 門檻 issue 39 保留開啟。

依據：[Codex config](https://learn.chatgpt.com/docs/config-file/config-reference)、[Claude CLI](https://code.claude.com/docs/en/cli-reference)、[Claude 環境變數](https://code.claude.com/docs/en/env-vars)、[bare 認證限制](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)。上述均以實際本機版本驗證，非未來版本通用保證。

### 續測實際數字

每題型每 arm 只有一筆、全程直接 native CLI cold，並非公開 warm API 的延遲基準。藍色物件＋不可信工具指令 state，noul >0.5／choice=blue／score>0.5 的簡單語意檢查皆通過。cache read/write 皆 0，完整 CLI aggregate usage 如下：

| 候選／題型 | 原 input → 候選 | 原 output → 候選 | 原秒 → 候選 |
|---|---:|---:|---:|
| schema-dedup-research／noul | 1553 → 1508 | 822 → 646 | 7.9126 → 6.6684 |
| thinking-off-research／noul | 1553 → 1376 | 822 → 58 | 7.9126 → 1.9513 |
| schema-dedup-research／choice | 1620 → 1557 | 517 → 632 | 4.6556 → 6.2391 |
| thinking-off-research／choice | 1620 → 1441 | 517 → 65 | 4.6556 → 1.6522 |
| schema-dedup-research／score | 1601 → 1539 | 2095 → 470 | 16.9972 → 4.2477 |
| thinking-off-research／score | 1601 → 1424 | 2095 → 61 | 16.9972 → 2.0833 |

Schema 去重的 input 減少 2.90%／3.89%／3.87%，輸出／時間仍有波動。MAX_THINKING_TOKENS=0 的 input 減少 11.40%／11.05%／11.06%，output 減少 92.94%／87.43%／97.09%；這會改變推理，尚未覆蓋困難／模糊／跨模型／實務概率品質。受控 mock 原版 thinking.type=enabled、budget_tokens=31999；那是上限，不代表每題用滿。thinking-off mock 確認 type=disabled，StructuredOutput 及其限制仍保留；CLI 原訂閱 auth 沿用。

CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=1 在固定 Bridge --system-prompt 下，mock system 估算同為155、messages 545–546，未見有意義額外減量，故沒有浪費真訂閱重測。8 次續測 mock 不消耗模型用量。兩個有效候選均未寫入產品程式／owner 設定或部署；正式仍為已驗的 0.9.11。

### 延遲與成本限制

Codex Decisions 本次公開中位數 5.7949→9.0641 秒；本機 inference_ms 約 4.421→5.821 秒，本機 total 約4.843→6.248秒，queue_wait_ms 都是0、provider setup 約百餘毫秒、每筆真 warm 1／cold0，1/1完整 receipt。外部總時間也含 Worker／網路時間，不能把全部變慢歸因單一元件，亦沒有 Bridge 重送證據。

Codex Chat 舊版兩題 cached_tokens=2432、新版兩題為0；雖 input 減少15.73%，本輪 OpenRouter牌價折算每題 cost 約0.00167→0.005312 USD，受到cache差異影響。因此不宣稱費用或實際訂閱額度也下降相同比例，這些數字不是額外 API 帳單；需更多快取狀態一致的樣本。

本輪總計31次真實推論 CLI（8前測＋6型別／隔離＋3升級＋8後測＋6續測），合計 64,062 input／7,686 output tokens；每題只啟動一次CLI、全程串行，原生CLI內部可能多步，沒有Bridge自動重送。另12次 credential-free mock（4版本驗收＋8續測），及隔離原生 close event 重現均不發動訂閱推論。所有測試Key已撤銷，原Key保留。
