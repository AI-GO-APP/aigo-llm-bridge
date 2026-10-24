# #39：單次使用 warm CLI 原型

2026-10-24 owner 授權開始試作。這是獨立實驗，正式安裝仍為 0.9.7-mac.1；沒有建立產品常駐池、修改設定或發布候選。原型只納入 Codex initialize／initialized 握手，請求到達後才建立 ephemeral thread 及 turn，完成即銷毀程序。Claude restricted print 的同等可觀測 ready 邊界仍待驗，不將「程序還活著／stdin 尚未關閉」視為 ready。

## 後台設定契約

owner 補充：成功後後台須讓使用者依機器能力手動設定常駐數量與併發上限，常駐設為零即關閉。

- `0 ≤ 常駐總數 ≤ 執行併發上限 ≤ 受理總數 ≤ 64`，各值為整數，執行併發至少 1，不能接受 bool。併發上限是 inference_workers，不是較大的 inference_pending。
- Claude、Codex 的常駐配額合計不得超過常駐總數；不能讓兩 provider 各自取得整份裝置配額。模型、Key 及 system instructions 不參與預熱；同一程序只屬於一筆推論，多題 Decisions 每題用新程序。
- active、warm、refill、closing 共同占用同一份程序名額。滿載時優先處理已受理請求，不另外補滿常駐；沒有 warm 時可在空餘名額 cold 啟動。已可能開始推論後不補送。
- 兩值必須原子驗證／套用，先 pause、停止補池、清理待命並 drain，再變更。降低上限不得暫時超額；常駐改為零後清空所有待命程序，保留一般 cold 執行。未通過能力／效能驗收的 provider 不提供啟用控制；預設零。
- 不依 CPU 核心數猜測訂閱吞吐，不自動覆寫 owner 設定；後台須呈現有效配置及 active／warm／refill 狀態。控制項真正開放時，另補六頁深淺色／窄版／Windows 適配卡驗收。

本次只在原型 RAM 中提供 resident／concurrency 及 pause/drain/configure；**尚無新的 SQLite setting、管理 API 或後台 UI**。這些控制項以本節為後續實作及驗收契約，不能聲稱現在管理台已提供。

## 程式與邊界

`desktop_bridge/codex_session.py` 封裝既有 cold protocol 的有界 stdio transport：單行 4 MB、未處理原始事件合計 8 MB 且最多 4096 筆；stderr 持續丟棄。claim 前只可 initialize／initialized，其他工作事件令程序失效。claim 只可一次且 cwd 相同；模型／ephemeral／事件 thread ID 仍核對。清理後移除事件 buffer，不將原文、事件或 stderr 寫入報告。

`tools/warm_cli_pool.py` 只供實驗使用，production Runtime 不建立它。單個 bounded refill thread、3 秒握手期限、100 ms–5 秒失敗退避、待命 TTL 最多 600 秒。auth／CLI 設定 stat generation 改變淘汰待命，provider 在 auth status 後、thread/start 前再次核對。pause 清理待命，包括 pause 時仍在建立的程序。清理失敗保留 counted quarantined slot 並停止補池，不釋出虛假容量。

現階段上限是原型自身的 CLI root 數；**尚未整合正式 Runtime 的全裝置推論／控制程序預算，也沒有 Mac 的 RSS／CPU hard limit**。RSS、fd、子孫程序及跨 provider 的整體 admission 是整合前的必要門檻，不能將 root 數或小量測試當作通過。CLI 自身可能還有 metadata／上游活動，零 turn 不能宣稱所有網路流量為零。

## 執行原型

```sh
python tools/benchmark_warm_cli.py --apply --idle-seconds 600 --requests 3 --resident 2 --concurrency 8 --output /tmp/warm-pilot.json
```

僅 Mac 可執行，未加 --apply 不啟動 CLI；requests=0 可只驗待命。以 read-only SQLite 讀取原安裝 CLI 路徑與期限，不開 Store、不讀 client Key、不改 owner 設定或服務。合成內容只在 stdin／RAM，各 arm 都用同一原型程序帳本；cold arm 將 resident 設零，warm arm 明確等握手就緒。整段 wall time 包含預熱／idle／補池，另記單請求延遲。取樣及 metadata 報告不得保存原始內容。小量單筆對照不等於 64 burst／持續吞吐、API receipt、真跨 Key 或跨模型驗收。

## 固定放行門檻（不因試作結果降低）

沿用 [#39](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/39)：至少 100 對跨 Key／model／system 的真合成隔離請求，含多題 Decisions；取消／逾時只終止自己程序，開始後 crash／斷線不增加推論，保留 known／unknown receipt。每 provider cold／warm 各三輪單筆、64 burst、三波連續 64，完整計入補池與全部 usage。burst p95 至少改善 15%、持續 good RPM 不下降超過 5%、正確率／timeout／38 秒達成率不變差、peak tree RSS 不增加超過 25%，另明定全裝置程序／fd／CPU 預算。idle 十分鐘零推論、stop 五秒內無自有程序／pipe／cwd。Mac／Windows 分別實測，未通過維持零。

原型的 100 對 fake CLI transport 測試不是上述真訂閱放行證明。不要用 mock、單筆 p95、未收到 usage event 或程序存活代替對應門檻。[本輪收據](qa/2026-10-24-macos-warm-cli-pilot.md)區分已驗與待驗。

協定依據：[Codex app-server](https://learn.chatgpt.com/docs/app-server) 的 initialize／initialized 與 thread／turn lifecycle；[Claude CLI](https://code.claude.com/docs/en/cli-reference) 的 restricted print／stream-json。沒有使用私有供應商端點或共用對話 session。
