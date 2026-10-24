# Mac 0.9.11 CLI token 精簡與發布驗收

日期：2026-10-24。Refs #46；完整 warm 放行門檻仍追蹤 issue 39。

## 狀態

候選實作中；尚未宣稱發布或更新 owner。前版正式為 0.9.10-mac.1／常駐 2／workers 64／pending 64。發布後在本收據補上不可覆寫 Release、來源 SHA、公開下載 hash、原 profile 更新及真 API 結果。

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
