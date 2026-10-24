# Mac #39 warm CLI 可行性原型

日期：2026-10-24。狀態：實作中，預設關閉；正式 0.9.7-mac.1、原 profile／Worker／URL／Key 未變。

新增 Codex 單次使用 transport 與獨立 pool／實機工具，詳見 [契約與門檻](../WARM-CLI-PLAN.md)。owner 要求的「常駐設零可關閉、不得大於併發上限」已納入 RAM 原型規則及後台規格；沒有宣稱管理台已開放此功能。

## 已驗範圍

- fake CLI 真子程序：100 對跨 routing marker／model／system 的 transport 隔離，PID 不重用、用量與事件不混線；不是 HTTP Key 授權或真訂閱模型驗證。
- 單一取消不影響另一工作；逾時／crash 無推論重送；一程序不可再次 claim；外來 thread 事件拒絕；長行／事件佇列有界；握手／reader 啟動失敗清理。
- generation 改變、TTL、pause during refill、設定零、resident 大於 concurrency 拒絕、共用 root 上限與失敗退避；cleanup 失敗保留 slot 並停止補池。
- 多題 Decisions 透過 Runtime／新 lease 驗固定結構與 receipt；第二題 crash 時保留第一題成本、started=2／completed=1、complete=false，不回部分成功。

## 實機與狀態

十分鐘 Codex initialize-only 待命與小量 cold／warm 對照執行中。最終數值於工具完成後補入；目前不得宣稱效能放行。

仍待完整真跨 Key／model／system 隔離、每 provider 64 burst／三波持續各三輪、全裝置 RSS／CPU／fd budget、Claude ready 邊界、Windows 獨立驗收與後台 UI。未通過上述門檻前維持關閉，不合併為已完成 #39、不發布或替換正式服務。
