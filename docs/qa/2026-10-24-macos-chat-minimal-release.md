# Mac 0.9.12 純 Chat 整合與部署驗收

2026-10-24。Refs #46，R-25／D-44；完整 warm 門檻仍追蹤 issue 39。

## 狀態

**已合併、公開發布、匿名下載／ZIP 真安裝，並更新這台 Mac 的原 profile。正式 0.9.12-mac.1，常駐合計2（純 Chat／standard 各1）、workers64／pending64。原 URL、設定、58筆舊Key rows及3把有效owner Key保留。**

## 範圍與取捨

只有 Mac 已驗 CLI binary 0.163.0-alpha.11／gpt-6.1-sol 的無 schema／tools／images 文字 Chat 選 codex-chat-minimal-v1；完整保留 caller system／developer／歷史，只移除 Bridge 固定提示與不使用的 CLI agent 工具／context。公開 catalog 只含衍生模型 metadata，來源／hash／改動與 Apache license／notice 隨包交付。

Decisions StructuredOutput、formatter、thinking、typed validator 與原 Chat schema／tools／images 路徑保持 standard。未知 CLI／模型／平台／catalog 先選 standard，收據明示原因；有效設定或 session profile 衝突則 503、在 turn 前停止，開始後不另送一次。兩 profile 共用一份 resident／workers 預算，target=2 為各1，0 可關閉常駐；一程序一題與原 auth／TTL／取消／pause／drain／closing 隔離維持。

## 本機驗證

- 6 次 credential-free native loopback：英文 500／1000／2000、中文 500、warm 500 及 standard Decisions；純 Chat tools／additional_tools 空，caller hash 完整、無 Authorization header、無 rollout，清理通過。warm ready 前 thread／turn／skills 都是0，config/read=1；租用後 config/read=2、skills／thread／turn 各1。standard Decisions 外層宣告保持原樣。
- 6 次直接原生訂閱 CLI，並行1、Bridge無重送：英文 input 506／1006／2006，中文 500 估算 input506，歷史30、不可信指令41；全部固定語意、實際模型、完整 usage 與清理通過。500 是 o200k_base caller 估算，沒有真 OpenRouter receipt。小樣本時間不建立 p95／SLA。
- 完整 Bridge／tools／Windows packaging 回歸 497 passed／23 skipped，Worker relay 13 passed；產品文件、品牌、版本及 diff whitespace 通過。私有 terms 清單本機未提供，由 PR CI secret 執行 required gate。
- 真 Cocoa 全頁／五步、深淺與 1200／480 寬，以及原生剪貼簿、CSV Save／Cancel、關閉 Key 清除、導覽限制與關窗後服務通過；65 張原生截圖保留在本機 probe 目錄。
- 升級前4次公開API同題基線通過，原 profile 0.9.11、常駐2／64／64；同一RAM測試Key跨升級後完成6項驗收；結束時已撤銷，清理腳本方法名稱錯誤與補清理見下方。
- 完整 pre-release native wire／訂閱用量 metadata 見 [證據](../concurrency-evidence/macos-0912-chat-minimal-2026-10-24.md)。
- 修正 native console probe 在觸發關閉後立即讀取欄位的競態：使用現有 bounded wait 等待真正清除 Key，通過條件仍是實際 DOM 空值，沒有略過或降低檢查。

## 正式交付門檻

完整 Bridge／tools／Windows packaging／Worker tests、品牌／terms／文件／版本、Cocoa 六頁與五步深淺／窄版／剪貼簿／CSV／生命週期、green PR→Mac release→匿名四附件／hash→真 ZIP 安裝／單機互斥→原 profile 更新及同 Key 公開 Chat／Decisions／schema／tool 收據。原 Worker 不需部署。候選只限對應 CLI／模型，Windows 沒有本輪純 Chat native 訂閱驗收。

## 合併、發布與原機部署

- 實作 [PR #53](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/53)，來源 `fb9421d5aa3e2dad1f6c991dbd418d4191cbfe12`。
- PR 全部 CI 成功：core [40078097113](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40078097113)、Mac [40078097136](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40078097136)、Windows [40078097147](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40078097147)、installer [40078097145](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40078097145)。main 的對應 CI 也全數通過。
- [Mac source Release](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.12-mac.1)，發布 [40078604442](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40078604442) 首輪成功；4個附件匿名下載，clean manifest／commit／self-test／size／SHA256 核對通過，core與data／license bytes吻合reviewed source。
- ZIP SHA256 `87e07553a5f53bbbc57f7a1797a068cd8b37be9ed32f0e1abcdef0e360a664ba`。從公開下載包真安裝、原生啟停、第二profile在DB前拒絕、結束API關閉通過；此時原服務先排空停止，驗完恢復，沒有同機第二套正式runtime。
- 原安裝從0.9.11原地更新，工具1.4174秒完成；manifest／HTTP版本／來源SHA／data-dir一致。50個core檔與公開data／license吻合，native profile gate=verified，舊設定全保留。沒有Worker部署或Windows release。
- 部署後乾淨停止0.6892秒：3個自有程序、2個空cwd全清；重啟idle2、兩profile各1，64/64、running/queued/refill_failures均0。0.9.11 app／previous manifest保留供回復，未回滾新DB。

## 同題公開 HTTPS 前後對照

每格僅1筆，兩來源同模型、相同request bytes/hash、同一臨時Key跨升級，常駐合計2、workers/pending64；全程串行，Bridge無推論重送。cache read/write均0，16次真CLI總用量包含原生內部步驟，不能只按答案文字估算。

| 模型／API | 0.9.11 input／output | 0.9.12 input／output | 秒數前→後 | 後版profile |
|---|---:|---:|---:|---|
| Codex／500文字Chat | 3129／6 | 506／6 | 9.9703→9.1517 | minimal，真warm1 |
| Codex／Decisions | 2789／41 | 2791／50 | 11.6548→6.9002 | standard，真warm1 |
| Claude／500文字Chat | 1060／85 | 1062／104 | 8.1055→4.2366 | standard，cold1 |
| Claude／Decisions | 1546／358 | 3674／711 | 8.0527→8.6464 | standard，cold1 |

Codex 500是o200k caller估算，後版input506＋output6＝total512，實際input比前版少83.83%。兩版output同6、cache同0；OpenRouter公開牌價折算cost為0.006318→0.001072 USD，這不是實際OpenRouter扣款或訂閱額度餘額。尚無同題OpenRouter receipt，不宣稱一比一用量等價。

Decisions與Claude程式／StructuredOutput／thinking未改，本輪不宣稱省其用量。Claude Decisions後筆input3674明顯較高，完整保留，不能混入純Chat成果；Bridge receipt仍1/1 complete、沒有Bridge重送，但未收集原生逐回合metadata，無法僅憑此收據判斷特定內部步驟。小樣本與不同時段不足以建立延遲因果、p95／吞吐或實務概率品質。

升級後外部JSON schema回status=ok、tool proposal回echo_marker，均standard／warm1／1次CLI及完整billing；input分別2658／2869，output15／56。這些保留既有相容路徑，未冒稱也已精簡。

共10次公開API（前4後6）與6次pre-release原生CLI，**16次CLI呼叫、26,179 input／1,481 output**；native內部回合仍可能多步，全部依CLI aggregate usage計量。另6次credential-free mock及read-only設定檢查不發動真模型。公開與生命週期metadata補於 [完整證據](../concurrency-evidence/macos-0912-chat-minimal-2026-10-24.md)。

## 清理與限制

同Key的10筆API全部成功後，驗收腳本finally誤用不存在的Store.revoke_key，腳本非零退出。以原快照確認唯一新Key及專用label後，使用正確Store.revoke補撤銷；沒有重跑任何推論或改owner Key。保留cleanup_error／cleanup_repaired證據，不把第一次清理當成功。最終59筆Key rows，58筆原rows逐筆hash相同，3把有效owner Key，唯一新測試Key已撤銷；原個人Codex config hash相同。

本次成功只放行已驗binary／gpt-6.1-sol文字Chat；其他模型／CLI／schema／tools／images與Claude仍standard。兩profile容量與隔離已有fake/native及正式小量證據，完整issue39持續64／CPU／RSS／跨平台門檻未完成。重新啟動後公開health200／device_online=true只作路由證據，真推論另以上表驗收，不互代。
