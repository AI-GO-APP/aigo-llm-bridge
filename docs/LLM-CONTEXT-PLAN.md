# 一般 LLM 接近原生 API token 用量的計畫

2026-10-24，Refs #46，D-43。**研究候選，尚未整合 runtime／發布**；正式 Mac 仍為 0.9.11-mac.1、常駐 2／workers 64／pending 64。本計畫不改 Decisions 的 StructuredOutput、formatter、thinking、schema 或 typed validator。實測與限制見 [研究 QA](qa/2026-10-24-macos-llm-structural-context.md)。

## 目標及計量

一般 Chat 不應為不會使用的編程工具、環境、權限說明及代理協作規則付出大量固定 input。以相同模型、完整 caller 訊息與格式要求呼叫 OpenRouter 的實際 usage 為對照，Bridge 應盡量接近；不能截短、摘要或重寫 caller 內容來取得漂亮數字。

候選放行門檻：固定短題及 500／1,000／2,000 reference input-token 題組，至少中英、system／developer、支援的歷史訊息與不可信指令案例。500–2,000 題組每筆完整 input 與參考差值不超過 `max(64 tokens, reference input × 10%)`。短題另報固定 overhead；不要求短題的百分比與長題相同。這是新候選門檻，尚未通過全題組或真 OpenRouter 對照。

分開記錄完整 input、output、total、cache read/write、reasoning、原生推論步驟、成功／失敗及成本。呼叫端若說「500 token」指 total，就以真 total 比較，不能只報 input。模型版本／努力程度／caller bytes／schema／tools／輸出要求必須相同；模型可見的隱藏指令仍可能不同，差異必須揭露。回應品質須通過固定語意檢查，不能靠關閉推理或縮短答案宣稱等價。小量單題不能推估 p95／訂閱額度／帳單等比例節省。

目前的 500 是 `o200k_base` 對固定 caller 文字的估算，**不是 OpenRouter 收據**。Codex 真實 input 3,127→547→506、output 都是 6；最精簡候選 total 512。Claude 同份文字 input 1,061→1,022，output 104→77；估算器不等於 Claude tokenizer。尚無實際 OpenRouter KEY／receipt，本輪沒有取得或使用其憑證。

## 結構性根因與可行方向

Codex 0.163.0-alpha.11 的對應公開模型目錄將 gpt-6.1-sol 指定為 `code_mode_only`；模型資訊優先於一般 feature flag。因此先前禁用 code_mode 與內層 namespace，仍留下外層 exec／wait／ask。改用 exec 或相同 harness 的 SDK，並不自動成為純推論。

本輪使用原生 CLI 的 `model_catalog_json` 啟動覆寫，僅在獨立子程序選定模型的 metadata 改為 direct、shell disabled、apply_patch null、experimental tools 空；另停用 request-user-input 及 CLI 自動附加的環境／協作／權限文字。首段候選保留既有 Bridge base/developer instructions；原生訂閱登入、實際模型、技能清單 fail-closed、read-only sandbox、never approval、ephemeral 與一程序一題皆保留。沒有改全域設定、CLI 二進位或私有 transport。

這移除的是模型輸入中的無關宣告；工具執行拒絕、程序限制、管理員 requirements 與事件檢查仍要獨立成立，不能只依靠「prompt 說沒有工具」。受控 mock 已見 tools 空、additional_tools 空及相同 caller hash；首段真訂閱短題 2,634→52、500 文字 3,127→547。再移除 Bridge 自己加上的固定 base/developer 提示，原封保留 caller system／developer／歷史，短題降至 11、500 文字降至 **506**。普通單一 user 文字題與 caller 估算差 6；有 system 或歷史時角色／訊息協定仍有不同開銷，不宣稱全部只差 6 或零成本。

Claude 2.1.306 在 tools／MCP 皆空、替換 system prompt 後，仍加入環境及模型等 system-reminder。縮短 Bridge 固定提示及移除空 instructions/schema wrapper 只省約 38–39 input。文字改 native stream-json 也沒有移除提醒。官方 `--bare`／`CLAUDE_CODE_SIMPLE=1` 不讀 OAuth／Keychain，故不能當成保持訂閱的解法。官方依據及對應來源版本見 QA。

## 實作分段與退出條件

### 研究段：已完成的小量可行性

- credential-free loopback 拆出工具／context；只存 allowlist metadata、長度與 hash，原始 request／response／event／stderr 不落檔。
- 原生訂閱 Codex 12 次、Claude 4 次，串行、無推論重送；同模型、完整 usage、固定語意及程序清理通過。
- Codex 歷史／指令隔離、caller JSON schema、initialize-only 待命後單次領取均有正面小樣本。這不是完整 API／常駐／品質矩陣。
- 確認 catalog **在 app-server 啟動載入**；只放 thread/start config 時仍留下 CodeMode 工具。不能把此候選直接塞進現有無 profile 的池。

### 整合段：先做 Codex 一般文字 Chat

1. 新增明確的 `chat-minimal` 與 `standard` 執行 profile。僅已驗原生 CLI／模型組合、普通文字 Chat 且無 generated_schema 走候選；使用 caller-only instructions，保留所有 caller 角色／內容而不再插入固定 Bridge prompt。Decisions 一律 standard。外部 schema／tools／image 先走原有相容路徑，逐項通過後再擴大。此次 caller JSON schema 單筆成功不等於完整支援已放行。
2. 不在執行時抓未固定的網路模型 JSON，也不把實驗用單模型檔當完整產品目錄。訂定來源 commit、license、schema、原生版本／binary fingerprint、原始與變更欄位 hash；僅採明確驗證的最小 metadata 差異，避免改 entitlement／模型 ID／context window／transport。模型探索／refresh 與訂閱權限依原有流程，不以客製 catalog 證明可用。
3. 未知 CLI／模型、managed requirements 衝突或缺必要能力，在**推論前**選定原有 profile 並明確標示未精簡，或拒絕候選；不能靜默宣稱 near-parity。推論一旦開始，不因錯誤／格式／timeout 自動另送一次。不得繞過管理員設定。
4. pool resource 帶不可變 profile／catalog generation；只租相符資源。仍是一個容量帳本，所有 provider／profile 的 active＋idle＋starting＋closing 共用原 workers 上限，常駐**合計**仍為 2，不得各自變成 2 或 64。先允許 minimal cold、standard warm 的安全整合，再在同一池加入 profile 選擇及已驗的 resident 分配；不可另外開一套不受原預算管控的候選程序。
5. 所有 caller 動態內容走 stdin／RAM；catalog 檔只含已審查公開 metadata。原 auth generation、撤 Key、取消／期限、pause/drain/stop、單次使用、ephemeral、未知用量及完整 billing 契約保留。profile／版本可留 allowlist metadata，任意旗標／prompt／catalog 原文不可進 log。

整合 gate：fake/native loopback 驗證原文與角色順序、工具清單空、無磁碟 session；跨 Key／model／system、錯 profile 拒絕、managed 衝突、版本失配、catalog 損壞、auth generation、TTL、取消與超時、關閉失敗及 refill 全數回歸。小容量 deterministic 混合 Chat／Decisions 證明總預算與常駐不變，真訂閱只跑必要少量。Decisions 指令、StructuredOutput、typed validation 與 usage 保持原基準；不重做本次未改的 thinking／formatter 優化。

### Mac 交付段：實際 API 與 near-parity 分層

整合後依 [Mac Release](MACOS-RELEASE.md) 完成共用／Worker／文件／品牌／terms／版本、原生六頁與生命週期、green PR 合併、公開 ZIP hash／真安裝／原 profile 升級及公開 HTTPS Chat／Decisions regression。對照同機同模型 cold／warm，分開報 token、延遲與補池成本；完整 #39 效能／隔離門檻仍獨立。只有公開 API 與已安裝版本也通過，才能稱候選已上線。

取得明確授權的真 OpenRouter 對照後才驗上述 near-parity 門檻；先用 provider 原生 usage 與 estimator 查固定成本的進展，不冒稱 OR 一比一。未取得對照不阻擋記錄研究成果，亦不能偽造完成證據。

### Claude 根本解法及備選

優先尋找／要求上游提供**保留訂閱原生登入**、可明確關閉 context reminder 與所有 agent 工具的 headless inference 模式；先在 repo 留重現與需求，沒有授權不代使用者對外發訊息。SDK 若共用相同 harness，須先證明 wire 有差異，再花訂閱測試。

可選的官方 API-key adapter 能提供更直接的 API 輸入，但它需要使用者自有 API KEY 與獨立帳務；不是現有訂閱的零成本替代，也不作自動 fallback。Codex 若日後官方設定失效，再評估公開原始碼的最小 CLI／上游修改、可重現建置與授權相容；本輪不需要 fork。兩者皆不採憑證抽取、私接訂閱 endpoint、修補個人 CLI、攔截正式 OAuth 或跨 caller 共用 thread。
