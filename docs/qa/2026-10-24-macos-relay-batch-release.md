# Mac 0.9.13：Relay重用與有界批次

2026-10-24。Refs #39／#46，R-26／D-46。此為候選實作與測試紀錄；尚未合併、發布、更新正式Bridge或部署Worker。正式仍0.9.12-mac.1／Worker0.9.4-relay，owner維持4＋4／64／64，Claude cold。Decisions StructuredOutput／thinking／prompt與caller schema不動。

## 實作與驗收門檻

直連certifi TLS、拒絕redirect、同origin keep-alive；poll1／result8／loopback72分離。含executor等待的派送總數≤72，Worker原64推論＋8控制容量不變。batch1–8，完整UTF-8 JSON≤6.1MB；整批驗證、FIFO、有效期內UUID去重、停止關閉自有連線、session隔離、任何HTTP送出後失敗不重送。系統代理保持原urllib，沒有直連停止速度／重用承諾；本Mac沒有proxy。

必要證據：真TLS／截斷／大小／timeout／redirect／停止與slot等待、pool隔離、72上限、跨poll去重、舊session、400成本headers；Worker單筆相容／encoded bytes／restart不重播。全產品回歸與真Cocoa六頁深淺／窄寬、五步、Windows卡、clipboard／CSV／關窗。clean合併後Mac公開四附件／匿名hash／ZIP真安裝／原profile更新；同帳戶Worker單獨部署。原Key rows／裝置／URL／模型／設定必須不變，測試Key撤銷。公開兩provider×Chat／Decisions固定題4筆及3×16＋64，逐題語意／model／profile／完整billing／DB成本一致且無Bridge重試；比較p50/p95／38秒內完成數與資源，不降低既有#39門檻。

## 候選本機檢查

- Bridge pytest：351 passed／18 skipped；包含當時15項新transport／Relay案例，真本機TLS重用／不信任憑證拒絕、慢速標頭總期限、stale socket不隱式重連實際執行。
- tools＋Windows packaging：161 passed／5 skipped；Mac歷史核心回歸33 passed；Windows platform JS 3 passed。這些不是Windows原生訂閱或發布證據。
- Worker＋研究回歸39 passed（正式Worker16、重播16、原型7）；凍結0.9.4 baseline，避免整合後比較到自己。
- 真Cocoa probe通過65張六頁／狀態／五步／Windows卡深淺×1200／480矩陣、native clipboard／NSSavePanel取消及儲存／CSV／關窗Key清除與服務保留。抽查窄版容量卡及寬版overview可讀。
- 文件覆蓋、branding、版本一致、diff檢查通過。本機`lint_terms --require`因沒有BANNED_TERMS／.banned-terms以exit1拒絕；不要求owner貼secret，首輪repo CI已帶secret執行通過；最終head仍須全CI通過才合併。

CI負面結果：441f635的Windows兩條回歸均在stop active read案例失敗（1秒後讀取執行緒仍活著），因此沒有合併／部署。不能將Mac的socket shutdown喚醒行為推及Windows。修正為連線建立後nonblocking HTTP讀寫，每≤50ms檢查停止與總deadline，HTTPResponse持有的Connection:close reader仍安全延後釋放；取消測試刻意令shutdown無效，並同時驗證header等待與close-response body等待。新增後共有17項transport案例（另驗partial write取消及2.4MB真TLS讀寫）；最終CI與完整回歸結果另補，不靠放寬1秒門檻繞過。

取消範圍：上述測試驗已建立連線的HTTP讀寫；尚在DNS／TLS建立或系統代理urllib中的等待仍依既有網路timeout，不聲稱所有平台／所有網路狀態均能50ms退出。模型開始後的未知結果仍不重送。

候選nonblocking transport亦透過原公開Worker無憑證GET health 3/3成功（1條TLS連線／2次reuse，1.2599／0.5241／0.5190秒），沒有模型呼叫；這只是傳輸連通證據，不能替代後續公開推論A/B。Node24.22.1在本機忽略目錄獨立安裝、官方SHA256核對，Wrangler4.152.0依repo lock安裝，沒有改全域Node／CLI登入；依賴稽核120 queries、0 advisories。

## 更新前正式基準

116/116有效，HTTP200、每題1/1完整billing、profile／模型／成本一致，Bridge inference retries=0。四筆serial依序Codex500 Chat、Codex Decisions、Claude500 Chat、Claude Decisions；input/output為506/6、2789/43、1062/168、1548/574，耗時6.3716／9.4182／4.4309／6.3780秒。500是本機tokenizer caller估算，沒有OpenRouter同題receipt。

| 批次 | 正確 | p50秒 | p95秒 | wall秒 | 38秒內 |
|---|---:|---:|---:|---:|---:|
|16 round1|16/16|13.6083|22.9914|23.0012|16|
|16 round2|16/16|11.3947|17.3614|17.3715|16|
|16 round3|16/16|11.9000|22.1704|22.1783|16|
|64|64/64|25.7672|45.5650|49.3977|49|

基準peak RSS 2,431,856 KiB、descendants23、fd2200、running11、pool roots19；health p95 0.0021秒。8GiB／8192fd只是測試階段間的升階guard，並非OS hard limit。原始metadata留本機忽略目錄，沒有request／response／credential內容。

基準控制工具未配置TTY，完成before後因stdin EOF結束；整體success=false只代表after未執行，不是116筆API失敗。finally已撤銷2把臨時Key，原Key rows／設定／profile目錄保留。保留原before report，不重新付費推論；後測使用新RAM臨時Key，不能宣稱此116筆與後測用相同Key。owner Key digest rows仍須跨更新逐一比對。

## 交付及後測

待本機完整檢查、CI、合併、Release、公開下載安裝、同Worker部署、原機更新與公開後測逐項補證。#39完整warm放行、Windows原生訂閱與真OpenRouter用量對照均不由本次transport測試代替。
