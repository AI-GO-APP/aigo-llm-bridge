# Mac 0.9.8 發布與小量公開 API 實測

2026-10-24 owner 授權的合併、Mac source Release、匿名下載校驗、公開 ZIP 實際安裝、原安裝更新及少量 LLM／Decisions 實測均已完成。正式版本 **0.9.8-mac.1**；warm CLI 工具保持預設關閉，production Runtime 不建立常駐池，後台控制項與 #39 的完整放行仍待驗。

## 來源與發布

- [PR #42](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/42) 已 squash merge，來源 `bc2dc90f09928f3068226dea6a3f68e612e20713`。
- [Mac Release](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.8-mac.1) 四個附件齊全，[正式發布工作流](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060624610) 全部通過；無覆寫既有 tag／附件。
- ZIP SHA256：`9fa252833a67df070e657a7fc5439f9cb31866503a193b44725e78fc5959790b`。匿名下載未使用 Authorization，manifest／self-test／size／SHA／source-release 與所有 runtime 模組及三份 opt-in 工具逐檔一致。
- 從公開 ZIP 建獨立安裝，真服務啟停、固定全機互斥、第二 profile 無 DB、64 名額與工具 --help 通過。先排空原服務，驗收後恢復舊服務，再經正式 source-update 更新同一 profile。
- 原安裝 health=ok、version=0.9.8-mac.1、accepting=true、64/64、queued/running=0。全部設定及 43 筆既有 Key rows（含歷次已撤銷測試 Key）保留，3 把原有效 Key 不變，所有本輪測試 Key 已撤銷。上一個穩定 0.9.7 程式／manifest 仍可回復，不回復或覆蓋 DB。

## CI 與修正

- 最終 head `8e74ec7`：[主 CI／私有 terms](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060121196)、[Mac](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060121287)、[Windows source](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060121189)、[Windows 原生安裝／升級](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060121256)、[依賴安全](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40060121197) 全綠。
- Windows 原生複製原先以 OpenClipboard(NULL) 清空後失去有效 owner，改用同一呼叫執行緒的自有 message-only window；成功移交記憶體、失敗釋放與視窗清理皆有回歸。保留真前端點擊、精確 clipboard readback、同 Key HTTP、A→B 更新及 disposable runner 電源還原，不調低驗收。依據：[Microsoft 契約](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard)。
- 較慢 runner 可能在驗證前就到期，排隊專用測試改為先確認 queued 再讓 monotonic budget 到期；仍要求 .9 秒內釋放、零 runner／零成本與補位，不將未觀測的 queue_wait 強改為零。此修正只有測試，沒有放寬 runtime 期限。
- 本機完整 442 passed／23 skipped；最終 packaging／provenance／API／clipboard 31 項與排隊 20 項通過，Worker 13、Windows adapter 3、branding／product docs／version／secret scan／diff 通過。Mac 真 Cocoa 六頁、深淺色／窄版、Windows 適配卡、真 Save／Cancel／clipboard、Key 清除、外部導覽與關視窗後服務通過。本機缺私有 terms 清單，由上述 CI 核實。

## 更新與小量公開 API

升級使用同一 RAM 臨時 Key 跨版本，模型目錄 200、原裝置／模型／Key／容量保留；公開 Codex Chat、JSON schema、工具提案、去重、unsupported_parameter=400、handoff 通過，原始回應不落磁碟。工具提案只回 JSON，未執行本機工具。

測速由**已安裝版本**的 `tools/benchmark_api_latency.py --apply --label after-0.9.8 --rounds 3` 執行：每模型每 API 三筆序列請求，Chat 固定短回覆、Decisions 一題 noul。12/12 都是 HTTP 200、實際模型符合、格式與完整一題 receipt／成本核對通過；沒有 inference retry。

| 模型 | API | n | HTTPS 中位數 s | HTTPS max s | Bridge 中位數 ms |
|---|---|---:|---:|---:|---:|
| openai/gpt-6.1-sol | chat | 3 | 7.2954 | 8.7676 | 3894 |
| openai/gpt-6.1-sol | decisions | 3 | 5.9220 | 8.0338 | 4438 |
| anthropic/claude-haiku-4.5 | chat | 3 | 3.6109 | 5.0104 | 1883 |
| anthropic/claude-haiku-4.5 | decisions | 3 | 7.1864 | 7.9393 | 4483 |

這是完整 HTTP 回覆時間，含 Worker／Relay／網路；不是首 token 時間。Bridge 耗時和 HTTPS 中位數來自各組各自的中位數，不能當成某一筆時間線相減。三筆只報中位數與 max，不宣稱 p95、高併發保證或 warm 效能放行。更新前每組僅一筆作路由／格式對照，不是配對三輪基準。

| 用量範圍 | 推論數 | input tokens | output tokens | 牌價換算 USD |
|---|---:|---:|---:|---:|
| 更新前對照 | 4 | 12839 | 1033 | 0.0208872 |
| 正式升級驗收 | 3 | 12843 | 78 | 0.0264660 |
| 更新後測速 | 12 | 31710 | 1722 | 0.0605722 |

本輪合計 19 次推論、57,392 input／2,833 output tokens、牌價換算約 US$0.1079254。token 包含 CLI 固定指令、模型推理與原生結構化 turns；短提示／短可見答案不代表 CLI 回報的全部 token 同樣少。費用是既有模型牌價換算，不宣稱是另付 API 帳單。

[完整 metadata](../concurrency-evidence/macos-098-release-2026-10-24.md) 含逐筆耗時、用量、receipt 檢查、來源／下載／安裝與保存證明，不含 body、答案、事件、stderr、client Key 或供應商憑證。

本輪沒有部署 Worker、切換訂閱登入、修改 owner 電源／鎖定或發布 Windows；原 HTTPS／device／Cloudflare 綁定／免費配額不變。warm pool 的未知錯誤分類、完整跨 Key／model 隔離、64 burst／持續／資源門檻、Claude ready 與後台 UI 仍由 #39 追蹤；本次合併發布不將其標示完成。
