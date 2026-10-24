# Mac 0.9.7-mac.1 階段 0–2：完成收據

Local Token Buffet Bridge 的 #36 階段 0–2 已合併、發布並更新原 Mac 安裝；warm CLI 池另列 [#39](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/39)。[發布與原安裝 metadata](../concurrency-evidence/macos-release-2026-10-24.md)記錄實際完成結果，不含 Key 或原始 I/O。

## 合併與來源

- [PR #40](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/40) 已合併，main 來源 `66a2c5364d7b7c9ebe29187cd0c2a7f1f48543ce`。
- 通過真訂閱的 runtime 為 `e637cfabc7e0a8f0057da3e46a9049d2ab5064bd`；後續僅改測試與文件，產品 runtime 逐檔相同。公開 ZIP 與正式安裝均已按 [最終模組 SHA256](../concurrency-evidence/macos-final-runtime-2026-10-24.json) 回讀，全部相符。
- 最終 PR head 1af6df7 的 [主要 CI／私有禁字](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054240491)、[Mac source／原生驗收](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054240514)、[Windows source](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054240501)、[Windows 隔離安裝／升級／所有權](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054240507)、[相依安全](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054240483) 全數通過。
- [Mac BYO source release](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40054773425) 全部通過，已建立不可覆寫的 [macos-source-v0.9.7-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.7-mac.1)，來源固定為上述 main SHA。

## 公開下載、安裝及原地更新

匿名下載四個公開附件：`aigo-llm-bridge-macos-source-0.9.7-mac.1.zip`、其 `.sha256`、`macos-source-manifest.json`、`macos-source-self-test.json`。未使用 Authorization header；manifest clean／redistributable 與 self-test success 均 true，ZIP／manifest／來源 receipt commit 一致。

ZIP SHA256：`adb0a3718d617a42ba457ee4d291421fb2e18aff2278d1f1f3bd345c55b5f9c5`。

排空並停止原服務後，以 repo 驗收工具實際安裝下載 ZIP。新安裝的 HTTP 版號／64 容量、同機第二 profile 拒絕且不建立 DB、停止後 socket 關閉全部通過；測試結束恢復原服務。此為無憑證／電源更動的可拋棄 profile，不替代首次自有帳戶部署。

從同一公開 ZIP 的解壓來源對原安裝執行 `mac_service.py update`。原使用版本為 0.9.5-mac.1，本輪曾依授權在原 profile 驗候選；最後正式 manifest 為 0.9.7-mac.1、來源 `66a2c53…`，source_checkout 指向保留的公開 ZIP 解壓目錄。已安裝 runtime 逐檔吻合公開來源及實測模組。

| 更新後驗收 | 結果 |
|---|---|
| 同一驗收 Key 更新前／後 GET models | 均 200；證明 Key 跨更新可用 |
| 原 profile／全部設定／28 筆原 Key rows | 完全相同；原有效 Key 仍為 3 把，沒有輪替 |
| 容量／原預設模型／URL／Worker／裝置 | 保留；64 workers／64 pending |
| Codex 真 HTTPS Chat／cost | `openai/gpt-6.1-sol`，200，7.912 s，cost 0.00845 USD 等值 |
| 同 UUID 去重／結構輸出／工具提案 | 通過；工具只提案，未執行本機工具 |
| unsupported_parameter／完整 handoff | 400／通過；handoff 只在 RAM 核對，未存 Key |
| Claude 真 HTTPS noul／receipt | 200／200，8.9241 s，cost 0.006742，單次 CLI 收據完整 |
| Claude 真 HTTPS choice＋score／receipt | 200／200，兩題答案／分布／confidence 有效，15.7967 s，cost 0.012707，calls_completed=2 |
| 臨時 Key／回復點 | 全數撤銷；保留 0.9.5-mac.1 穩定 manifest 為 rollback，未還原或替換 DB |

鎖定狀態僅讀取，Codex 驗收前後皆 false；沒有為驗收改動鎖定／電源。ZIP 內候選 QA 反映建置當時，正式公開下載與更新證據以本收據為準；不覆寫已發布 ZIP。

## 已完成的實機效能及 HTTPS

[完整 QA（含所有負面結果）](2026-10-24-macos-queue-decisions.md)與[機器可讀收據](../concurrency-evidence/macos-final-runtime-2026-10-24.json)保留每輪資料；沒有刪除失敗基線或重送推論。

- Haiku 4.5、固定 blue-object factual probe、64 workers／64 pending：候選三輪 192/192 正確，模型／格式／成本／完整 CLI 收據一致。Decisions p95 中位數 -22.74%、Chat -44.21%、good RPM +27.83%、peak tree RSS +18.82%，全部數值門檻通過。
- 原 Worker／URL 真 HTTPS 64/64 HTTP 200，完整成本收據、max 33.2171 s，均在 38 秒內。測試 Key 撤銷；不是以 health、401 或本機結果替代外部推論。
- 本機完整回歸 404 passed／23 skipped，Worker 13、Windows adapter JS 3；最後測試工具修正另 11 passed。最終來源另補合成 burst 384/384 與三波持續 384/384。

## 操作範圍與限制

原裝置設定檔、固定 URL、Cloudflare 帳戶／Worker、owner Key 與既有 CLI 登入是保留契約。未購買方案、部署新 Worker、改訂閱登入／電源／鎖定或發布 Windows。原工作區 AGENTS.local.md／.codex/config.toml 未提交或打包；既有 AGENTS.md／.gitignore 未提交變更已核對保留。

效能改善限於上述固定 probe，不保證任意模型／題目或校準品質。Claude 原生結構模式最多採 CLI turn 上限 2，仍為一次 Bridge CLI 呼叫，成本按實際 CLI token 合計；部分用量高於舊純提示模式。先前免費帳戶 DO 配額的 1101 本輪未重現，但沒有提高配額或做跨日可用性保證。
