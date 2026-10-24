# Mac #39 warm CLI 可行性原型

日期：2026-10-24。狀態：實作中，預設關閉；正式 0.9.7-mac.1、原 profile／Worker／URL／Key 未變。

新增 Codex 單次使用 transport 與獨立 pool／實機工具，詳見 [契約與門檻](../WARM-CLI-PLAN.md)。owner 要求的「常駐設零可關閉、不得大於併發上限」已納入 RAM 原型規則及後台規格；沒有宣稱管理台已開放此功能。

## 已驗範圍

- fake CLI 真子程序：100 對跨 routing marker／model／system 的 transport 隔離，PID 不重用、用量與事件不混線；不是 HTTP Key 授權或真訂閱模型驗證。
- 單一取消不影響另一工作；逾時／crash 無推論重送；一程序不可再次 claim；外來 thread 事件拒絕；長行／事件佇列有界；握手／reader 啟動失敗清理。
- generation 改變、TTL、pause during refill、設定零、resident 大於 concurrency 拒絕、共用 root 上限與失敗退避；cleanup 失敗保留 slot 並停止補池。
- 多題 Decisions 透過 Runtime／新 lease 驗固定結構與 receipt；第二題 crash 時保留第一題成本、started=2／completed=1、complete=false，不回部分成功。

## 實機與狀態

實機 Codex `0.163.0-alpha.11`／`gpt-6.1-sol`，resident=2、concurrency=8：

| 測項 | 結果 |
|---|---|
| initialize-only idle | 600.103 秒，thread/start=0、turn/start=0、work event=0；這是協定未送推論的證據，不量測個人 CLI 的帳戶總用量 |
| 第一組 cold／warm | 各 3 筆均正確、模型符合；中位數 3.5616／3.4759 秒（約改善 2.4%） |
| 固定 commit 確認組 cold／warm | 各 3 筆均正確、模型及非負完整 usage 符合；中位數 3.6514／3.3202 秒（約改善 9.1%） |
| 確認組 cold startup | spawn 1–2 ms、initialize ready 38–52 ms；遠小於本組約 2.7–3.9 秒 inference，未顯示 startup 為主要瓶頸 |
| 確認組 usage | cold prompt/completion 12620/27、warm 12622/27；cache cold 3072、warm 0，保留不同 cache 與網路／推論變異，不把差異全歸因預熱 |
| 補池成本 | 確認組六筆合計建立 14 個一次性 app-server，含等待後清理的未使用程序；成功握手合計 0.6121 秒，整段 21.4435 秒含預熱／補池，不隱藏額外啟動 |
| 確認組資源 | tree RSS 289088 KiB、descendant 4（含 sampler ps）、tree fd 255；CPU 38.9% 為 ps lifetime-average 取樣峰值，100%=一 logical core，非瞬時或 hard limit；161 samples、0 sampling errors |
| 停止 | 首組 0.0762 秒、確認組 0.0231 秒；自有 CLI 全停止、空 cwd 移除、pool total=0 |
| Claude 2.1.306 | restricted print stream-json、stdin 未送任何 bytes、等待 3.005 秒無事件；程序存活但未建立可驗證 ready 邊界，清理 0.019 秒；沒有實作 Claude warm pool |

確認組來源 `0b94385`，四份實際來源 hash 與逐筆數值見 [metadata](../concurrency-evidence/macos-warm-cli-pilot-2026-10-24.md)。首組執行於未提交原型，未捕捉來源 hash，且最初報告的 usage 篩選誤用原始欄位名而為空；已修正工具並另跑確認組，不將首組當成成本或 immutable release 證明。確認組是直接 provider pilot，沒有取代真 HTTP Key／receipt 驗收，也未用三筆計算或宣稱 burst p95。

兩組皆未證明 15% burst p95 或持續吞吐收益，且現有單筆 metrics 未顯示可預熱部分為主要瓶頸。因此本輪停留獨立試作、不放大為 64 常駐／完整推論矩陣，不啟用後台或正式服務。保留全部結果供後續針對尖峰啟動成本的測試判斷，不能推論所有負載都沒有收益。

仍待完整真跨 Key／model／system 隔離、每 provider 64 burst／三波持續各三輪、全裝置 RSS／CPU／fd budget、Claude ready 邊界、Windows 獨立驗收與後台 UI。未通過上述門檻前維持關閉，不合併為已完成 #39、不發布或替換正式服務。


## 回歸與限制

本機最終完整回歸 **434 passed、23 skipped**，原型／opt-in tests 29 項；Worker 13 項通過，branding／product docs／version／secret scan／diff 通過。主 CI [40058167721](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40058167721) 在確認組 commit 通過，含本機缺私有清單的 `lint_terms --require`；Mac／Windows CI 不等於 warm live gate。

一次較早的同時回歸中，fake 第二題 crash 的 receipt 正確保留 known/unknown，但分類曾為 generic server；後續獨立 100 次重複未重現，已加僅含例外類型的 test 診斷以定位。這個未解分類也是不放行整合的限制，不以重跑成功宣稱已修復。

[草稿 PR #42](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/42) 保持 open，#39 未結案；未發布 0.9.8 候選，正式 0.9.7-mac.1 health=ok、accepting=true、64/64、queued/running=0。工具對原 profile 僅使用 read-only SQLite，未建立測試 Key、修改設定、替換服務或操作 Worker。
