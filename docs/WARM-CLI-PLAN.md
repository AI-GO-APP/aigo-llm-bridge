# #39：單次使用 warm CLI 原型

2026-10-24 後續：0.9.12正式版依owner要求設總常駐8（minimal／standard各4），64/64維持；公開96筆與直連16筆全通過。公開64單波p95=55.6066秒、38秒內38/64，Runtime外等待明顯，尚不能放行完整效能門檻。實際本機peak running為公開10／直連16，不能把公開64起跑當本機64同時推論；詳見 [後續負載收據](qa/2026-10-24-macos-0912-staged-api.md)。下方2/64為先前operator試驗的歷史配置。

2026-10-24 owner 授權開始試作。初次試作以 0.9.7-mac.1 為正式基線，沒有建立產品常駐池。owner 後續明確授權合併、發布 Mac 0.9.8 與小量公開 API 實測；本次交付包含預設關閉的實驗工具與 cold transport，0.9.8 production Runtime 未建立 warm pool。owner 隨後明確要求正式 API 接入、2 個常駐／64 併發與小量開關實測；0.9.9 提供此 Mac operator 試驗，預設仍為零。此明確試驗不冒充完整效能放行。原型只納入 Codex initialize／initialized 握手，請求到達後才建立 ephemeral thread 及 turn，完成即銷毀程序。Claude restricted print 的同等可觀測 ready 邊界仍待驗，不將「程序還活著／stdin 尚未關閉」視為 ready。

## 後台設定契約

owner 補充：成功後後台須讓使用者依機器能力手動設定常駐數量與併發上限，常駐設為零即關閉。

- `0 ≤ 常駐總數 ≤ 執行併發上限 ≤ 受理總數 ≤ 64`，各值為整數，執行併發至少 1，不能接受 bool。併發上限是 inference_workers，不是較大的 inference_pending。
- Claude、Codex 的常駐配額合計不得超過常駐總數；不能讓兩 provider 各自取得整份裝置配額。模型、Key 及 system instructions 不參與預熱；同一程序只屬於一筆推論，多題 Decisions 每題用新程序。
- active、warm、refill、closing 共同占用同一份程序名額。滿載時優先處理已受理請求，不另外補滿常駐；沒有 warm 時可在空餘名額 cold 啟動。已可能開始推論後不補送。
- 兩值必須原子驗證／套用，先 pause、停止補池、清理待命並 drain，再變更。降低上限不得暫時超額；常駐改為零後清空所有待命程序，保留一般 cold 執行。未通過能力／效能驗收的 provider 不提供啟用控制；預設零。
- 不依 CPU 核心數猜測訂閱吞吐，不自動覆寫 owner 設定；後台須呈現有效配置及 active／warm／refill 狀態。控制項真正開放時，另補六頁深淺色／窄版／Windows 適配卡驗收。

0.9.9 將 inference_resident 存入 SQLite，管理台「常駐與併發」提供三值專用套用；須先暫停、排空，API 原子寫入並調整 live limit。Mac CLI 的 workers --resident 同樣保留原 profile，先驗參數再暫停／排空／重啟。其他安裝者不自動啟用；Windows 常駐尚未開放。

## 程式與邊界

`desktop_bridge/codex_session.py` 封裝既有 cold protocol 的有界 stdio transport：單行 4 MB、未處理原始事件合計 8 MB 且最多 4096 筆；stderr 持續丟棄。claim 前只可 initialize／initialized，其他工作事件令程序失效。claim 只可一次且 cwd 相同；模型／ephemeral／事件 thread ID 仍核對。清理後移除事件 buffer，不將原文、事件或 stderr 寫入報告。

`desktop_bridge/warm_pool.py` 由正式 Runtime 擁有；tools/warm_cli_pool.py 為原型相容 import。`warm_runtime.py` 僅初始化 Codex，不讀 caller 內容。單個 bounded refill thread、3 秒握手期限、100 ms–5 秒失敗退避、待命 TTL 最多 600 秒。auth／CLI 設定 stat generation 改變淘汰待命，provider 在 auth status 後、thread/start 前再次核對。pause 清理待命，包括 pause 時仍在建立的程序。清理失敗保留 counted quarantined slot 並停止補池，不釋出虛假容量。

0.9.9 中兩來源推論 root、idle、refill、closing 共用 inference_workers 名額。Claude cold 呼叫也先取同一名額，必要時淘汰 idle Codex；補池讓位於等候請求。唯讀 auth／model 控制程序及四個外部 schema 子程序仍屬既有獨立控制預算。此 root 上限不是全程序樹 RSS／CPU hard limit；子孫程序、RSS／fd／CPU 與完整尖峰收益仍須量測，不能將小量對照當作通過。CLI 自身可能還有 metadata／上游活動，零 turn 不能宣稱所有網路流量為零。

## 執行原型

```sh
python tools/benchmark_warm_cli.py --apply --idle-seconds 600 --requests 3 --resident 2 --concurrency 8 --output /tmp/warm-pilot.json
```

僅 Mac 可執行，未加 --apply 不啟動 CLI；requests=0 可只驗待命。以 read-only SQLite 讀取原安裝 CLI 路徑與期限，不開 Store、不讀 client Key、不改 owner 設定或服務。合成內容只在 stdin／RAM，各 arm 都用同一原型程序帳本；cold arm 將 resident 設零，warm arm 明確等握手就緒。整段 wall time 包含預熱／idle／補池，另記單請求延遲。工具會取樣自身整棵程序樹 RSS／CPU／fd 並記來源 hash；取樣及 metadata 報告不得保存原始內容。小量單筆對照不等於 64 burst／持續吞吐、API receipt、真跨 Key 或跨模型驗收。

## 固定放行門檻（不因試作結果降低）

沿用 [#39](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/39)：至少 100 對跨 Key／model／system 的真合成隔離請求，含多題 Decisions；取消／逾時只終止自己程序，開始後 crash／斷線不增加推論，保留 known／unknown receipt。每 provider cold／warm 各三輪單筆、64 burst、三波連續 64，完整計入補池與全部 usage。burst p95 至少改善 15%、持續 good RPM 不下降超過 5%、正確率／timeout／38 秒達成率不變差、peak tree RSS 不增加超過 25%，另明定全裝置程序／fd／CPU 預算。idle 十分鐘零推論、stop 五秒內無自有程序／pipe／cwd。Mac／Windows 分別實測；其他安裝者預設零。owner 明確授權的 Mac 2/64 operator 小量試驗是本輪限定範圍；一般效能推薦與完整驗收仍須上述門檻。

原型的 100 對 fake CLI transport 測試不是上述真訂閱放行證明。不要用 mock、單筆 p95、未收到 usage event 或程序存活代替對應門檻。[本輪收據](qa/2026-10-24-macos-warm-cli-pilot.md)區分已驗與待驗。

協定依據：[Codex app-server](https://learn.chatgpt.com/docs/app-server) 的 initialize／initialized 與 thread／turn lifecycle；[Claude CLI](https://code.claude.com/docs/en/cli-reference) 的 restricted print／stream-json。沒有使用私有供應商端點或共用對話 session。

## 已授權的 Mac 0.9.8 發布

發布收據見 [Mac 0.9.8](qa/2026-10-24-macos-warm-cli-release.md)。小量端到端工具為 `python tools/benchmark_api_latency.py --apply --label after --rounds 3 --output /tmp/api-latency.json`；每輪 Codex／Claude 各一筆 Chat 與一題 noul，序列執行、短輸出、零推論重送，公開 HTTPS 時間含 Relay／網路。數字 usage 可能包含 CLI 固定指令開銷，不宣稱全部輸入只有使用者提示長度。此測試不是 warm/cold 或尖峰效能放行。

## Mac 0.9.9 operator 試驗

正式 Chat 與 Decisions 共用 Runtime pool，每題各用新程序。取消、逾時、登出世代變更或程序失效均不重送推論；空目錄／管線清理完成才釋放名額，失敗保留 quarantined 並停止補池／拒絕新租用。暫停停止補池並清 idle；已受理工作可排空，停止時取消並關閉全部自有程序。TTL 120 秒，初始化期限 3 秒，補池退避 0.1–5 秒。

公開端對照用同版程式、同模型短輸入，以 resident=0 與 2 各做三筆 Chat、三筆 Decisions。每筆核對 receipt.execution、實際模型、成本及完整計量；warm arm 每筆前確認 idle=2。工具 `benchmark_api_latency.py --provider codex` 不重送推論；不支援任意 token 上限，CLI 固定指令／reasoning 用量全數列入。公開 HTTPS 延遲含網路／Relay，另記 Bridge 分段，不能從六筆單一模型宣稱 64 burst 收益或推廣至 Claude。最終保留 owner 指定 2/64，供後續外部使用者獨立基準。

0.9.9 已發布、從公開 ZIP 更新原機並完成上述小量正式 API 對照；測後保留 2/64，詳見 [實測與來源收據](qa/2026-10-24-macos-runtime-warm-pool.md)。warm 命中 6/6，不以此取代本文件一般放行門檻。
