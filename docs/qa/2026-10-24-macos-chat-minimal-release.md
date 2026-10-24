# Mac 0.9.12 純 Chat 整合與部署驗收

2026-10-24。Refs #46，R-25／D-44；完整 warm 門檻仍追蹤 issue 39。

## 狀態

實作候選；尚未合併、公開發布或更新原安裝。當前正式 0.9.11-mac.1，原 profile 2/64/64、URL／owner Key 保留。完成狀態須待下方新增實際發布及部署證據，不能以研究收據代替。

## 範圍與取捨

只有 Mac 已驗 CLI binary 0.163.0-alpha.11／gpt-6.1-sol 的無 schema／tools／images 文字 Chat 選 codex-chat-minimal-v1；完整保留 caller system／developer／歷史，只移除 Bridge 固定提示與不使用的 CLI agent 工具／context。公開 catalog 只含衍生模型 metadata，來源／hash／改動與 Apache license／notice 隨包交付。

Decisions StructuredOutput、formatter、thinking、typed validator 與原 Chat schema／tools／images 路徑保持 standard。未知 CLI／模型／平台／catalog 先選 standard，收據明示原因；有效設定或 session profile 衝突則 503、在 turn 前停止，開始後不另送一次。兩 profile 共用一份 resident／workers 預算，target=2 為各1，0 可關閉常駐；一程序一題與原 auth／TTL／取消／pause／drain／closing 隔離維持。

## 本機驗證

- 6 次 credential-free native loopback：英文 500／1000／2000、中文 500、warm 500 及 standard Decisions；純 Chat tools／additional_tools 空，caller hash 完整、無 Authorization header、無 rollout，清理通過。warm ready 前 thread／turn／skills 都是0，config/read=1；租用後 config/read=2、skills／thread／turn 各1。standard Decisions 外層宣告保持原樣。
- 6 次直接原生訂閱 CLI，並行1、Bridge無重送：英文 input 506／1006／2006，中文 500 估算 input506，歷史30、不可信指令41；全部固定語意、實際模型、完整 usage 與清理通過。500 是 o200k_base caller 估算，沒有真 OpenRouter receipt。小樣本時間不建立 p95／SLA。
- 完整 Bridge／tools／Windows packaging 回歸 497 passed／23 skipped，Worker relay 13 passed；產品文件、品牌、版本及 diff whitespace 通過。私有 terms 清單本機未提供，由 PR CI secret 執行 required gate。
- 真 Cocoa 全頁／五步、深淺與 1200／480 寬，以及原生剪貼簿、CSV Save／Cancel、關閉 Key 清除、導覽限制與關窗後服務通過；65 張原生截圖保留在本機 probe 目錄。
- 升級前4次公開API同題基線通過，原 profile 0.9.11、常駐2／64／64；測試 Key 暫存RAM等待同Key升級後驗收，部署完成或失敗退出時撤銷。
- 完整 pre-release native wire／訂閱用量 metadata 見 [證據](../concurrency-evidence/macos-0912-chat-minimal-2026-10-24.md)。
- 修正 native console probe 在觸發關閉後立即讀取欄位的競態：使用現有 bounded wait 等待真正清除 Key，通過條件仍是實際 DOM 空值，沒有略過或降低檢查。

## 正式交付門檻

完整 Bridge／tools／Windows packaging／Worker tests、品牌／terms／文件／版本、Cocoa 六頁與五步深淺／窄版／剪貼簿／CSV／生命週期、green PR→Mac release→匿名四附件／hash→真 ZIP 安裝／單機互斥→原 profile 更新及同 Key 公開 Chat／Decisions／schema／tool 收據。原 Worker 不需部署。候選只限對應 CLI／模型，Windows 沒有本輪純 Chat native 訂閱驗收。
