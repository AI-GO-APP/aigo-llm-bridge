# Mac 0.9.9：正式 API 常駐接入、公開發布與開關測速

已合併 [PR #44](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/44)、發布 [0.9.9-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.9-mac.1)，並從匿名下載的公開 ZIP 更新 owner 原 Mac 安裝。現在接受請求，常駐 **2**、執行上限 **64**、受理總數 **64**；2 個 Codex 初始化待命已就緒，原裝置／固定 endpoint／45 筆既有 Key rows 與 3 把有效 owner Key 保留。

這是 owner 明確指定的 Mac operator 試驗。其他 profile 預設 0；Claude 尚無已驗 ready 邊界，維持 cold。一般 64 burst／持續收益、真跨 Key／model／system 大矩陣、資源 hard limit 與 Windows 常駐驗收繼續由 issue 39 追蹤，本次不宣稱全數通過。

## 已交付的行為

正式 Chat 與每題 Decisions 都經同一個 Runtime pool：Codex 只預做 initialize／initialized，租用後才建立帶 caller 模型／內容的 ephemeral thread／turn，一程序只供一題，使用後關閉。兩 provider active／idle／refill／closing 共用 workers 名額；Claude cold 可淘汰 idle Codex，補池讓位給已受理工作，不額外把 64 變成 66。取消／逾時／崩潰不重送，已知及未知成本沿用 receipt；新增 execution.warm_hits/cold_starts 如實揭露。

管理台「連線與設定 → 常駐與併發」、本機專用 API 與 Mac workers --resident 支援原子三值設定；paused＋idle 才能套用，要求整數 `0 ≤ resident ≤ workers ≤ pending ≤ 64`，常駐 0 關閉。Windows 常駐欄停用，原容量設定仍可使用。

## 公開 HTTPS 開關對照

同一 0.9.9-mac.1、同一 gpt-6.1-sol 與固定短輸入，關閉 3 筆 Chat＋3 筆 Decisions，再開啟同樣 6 筆；每筆 warm 前等到 ready idle=2。12/12 正確格式／模型／成本／完整 receipt 通過，cold arm 6 cold／0 warm，warm arm 6 warm／0 cold。沒有推論重送；完整 HTTPS 時間包含 Relay／網路，Bridge 分段另存數值。

| API | 關閉中位數 | 常駐 2 中位數 | 中位數變化 | warm 命中 |
|---|---:|---:|---:|---:|
| LLM Chat | 4.3936s | 4.2353s | 快 3.6% | 3/3 |
| Decisions | 5.0333s | 4.6713s | 快 7.19% | 3/3 |

每格只有 3 個樣本，順序為 off 再 on；warm Decisions 有一筆原生 prompt cache read 3,072 tokens，其他樣本為 0，reasoning tokens 亦有差異。這些差值不是常駐池的獨立因果效果；不能據此推論 burst p95、持續吞吐或 Claude 的加速。warm 命中證明正式 API 使用預熱程序，不代表上游推論及網路延遲已下降。外部使用者的獨立時間基準由 owner 後續發動，本輪未代跑。測完已保留 2/64 並重新啟動驗待命就緒。

本輪升級驗收 3 次＋開關比較 12 次，共 15 次已完整計量 CLI 嘗試、64,003 input／306 output tokens，牌價換算 USD 0.1252292。短使用者輸入不等於全部 token 很少，CLI 固定指令／reasoning／原生結構 turn 都納入用量；這是訂閱消耗的牌價估算，不是另發出的 API 帳單。另有 1 筆預期的 unsupported_parameter 400，CLI 嘗試為 0。三把本輪臨時 Key 均撤銷，3 把原有效 Key 不動。

## 驗證與來源

來源 `2be8195037c304b988c46f8a48697486978b3592`，ZIP SHA256 `f3ac1fb5f028765c50e55c9e2beb2385c8a4ed82649f08eb53fad652c58989ef`。四附件匿名下載、hash／source、實際 ZIP 安裝、全機互斥與停止通過；原 profile 更新前後以同一臨時 Key 驗 public models、Chat／去重、JSON schema／tool proposal、unsupported_parameter，全部通過。沒有重建 Worker 或部署 Cloud，也沒有 Windows 發布、訂閱登入或電源／鎖定變更。

454 passed／23 skipped；Worker 13 passed。核心／私有 terms、Mac source／native／ZIP、Windows source、Windows installer 回歸均通過。Mac 實機六頁淺深色、1200／480、Mac 與 Windows 附加卡、新容量卡無溢出；接單中停用、非法 2>1 不寫入、合法 0/64/64、暫停／恢復、剪貼簿、CSV Save／Cancel、KEY 清空、關 viewer 後服務均通過。

實際 2 個待命時停止耗時 0.7116s，觀測到的自有程序／空 cwd 均清空；重啟後 resident=2、idle=2，保留可回復的前版 0.9.8 manifest 與相同 DB。此小量實機生命週期不冒充所有 crash／64 壓力情境。初次驗證 helper 在非同步重啟後太早讀 health，遇到尚未 listen 的連線拒絕；服務實際已恢復，helper 補上有期限的唯讀 readiness 等待後重驗通過，未改 runtime 或重送推論，失敗紀錄亦保留。

完整 allowlist metadata、CI IDs、每筆耗時／tokens／成本與設定／Key 保留布林見 [數字證據](../concurrency-evidence/macos-099-runtime-warm-2026-10-24.md)。
