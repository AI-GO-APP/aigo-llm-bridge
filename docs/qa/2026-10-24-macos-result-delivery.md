# Mac 0.9.14：已計算結果交付

2026-10-24，R-27／D-47，refs #39／#46。0.9.14已合併／發布／從公開ZIP更新，但正式後測20筆18有效，2筆Claude推論前預檢503；全部20筆結果皆交付，傳輸錯誤與結果補送均0。停止後續升階、撤銷測試Key並回復原機0.9.12-mac.1。後續[0.9.15冷Claude預檢修正](2026-10-24-macos-auth-preflight.md)另記。Worker0.9.5-relay及4＋4／64／64保留，沒有重送失敗推論。

## 問題與修正

0.9.13第3輪16筆有1筆外部95.4794秒408，但本機4.837秒已完成、11 input／6 output及成本完整入帳；result transport失敗1次。舊版沒有足夠錯誤分類，不能確認單一網路根因。另有一筆成功請求Runtime25.941秒，不能把所有尾延遲歸給Relay。

候選先丟棄已知可讀／EOF／超過10秒的idle socket，再送新request；HTTP exchange仍不自行重送。只對同一已計算result，暫時I/O／timeout／truncated／408／5xx最多補送一次、強制新連線、沿原deadline＋2秒；本機API／CLI完全不再呼叫。Worker原已先刪pending[id]才resolve caller，因此重複result不二次交付／不派新工作。401／403等明確拒絕與schema／size／stop／expiry不補送。ACK遺失後第二次accepted:false只表示不pending，保留未確認語意，不冒稱確認成功。

僅新增RAM固定數字／enum診斷。provider／Decisions StructuredOutput／thinking／caller內容／Key／裝置／共用容量不變，Worker code仍0.9.5，不需再次部署。0.9.13已在GitHub標示prerelease／驗收失敗；不刪除或覆寫附件。

## 驗收分層

必要：局部EOF送出前淘汰、送出後斷線不重跑local、同result暫時補送一次、新連線／最多2次、停止及永久拒絕不補送、ACK遺失／重複result一次resolve與未確認語意、真TLS及大body／partial IO／deadline／舊新版相容。再跑全產品、原生Cocoa／ZIP／CI、clean release／匿名下載安裝、原profile升級與同題公開兩provider×Chat／Decisions；3×16通過才做64。保留前兩輪所有失敗／用量，不以重跑取代失敗紀錄。#39完整warm效能與#46原生上下文異常均未因此關閉。

本機361 passed／18 skipped，含25項專項；Worker／研究41 passed，tools／Windows packaging161 passed／5 skipped；真Cocoa65畫面及clipboard／NSSavePanel／CSV／關窗檢查通過。版本／文件／branding／secrets／diff通過；本機沒有terms secret，合併仍要求repo CI的require檢查。

已做兩類零推論真傳輸：

- 原Worker的unknown result-ID POST，前版／候選各3×16、兩次31秒idle，96/96都200／accepted:false。前版reuse40／created8，候選reuse24／created24、idle_discarded16。沒有重現原失敗，不能宣稱證實idle是根因，亦不把額外建連稱作免費。
- 原機先正常停止，以只允許專用Key＋UUID的metadata-only loopback fixture暫代agent；其他請求回503 maintenance，沒有啟動Runtime／CLI。真原Worker先接受同ID result，外部已得到200 fixture；受控丟棄該ACK後補送一次，新TLS連線回accepted:false。local fixture1次、result2次、同work ID、外部body正確，DB requests列數不變，0推論；retries1／forward_errors0／not_pending1。這是結果去重／ACK遺失證據，不是模型或模型目錄能力證據。臨時Key撤銷，原服務／設定恢復。

原機回復0.9.12時，首次立即健康探測早於API啟動而ConnectionRefused；隨後正常start／readiness確認版號、4＋4／64／64，不以rollback命令exit0當正式恢復證據。CI／Release與正式真LLM後測仍待逐項補證。

## 0.9.14實際交付及正式失敗收據

[PR58](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/58) head4df32e2的5條CI全綠；來源00390bfd82660a9ce0ddfd9a937fece2a1585c2f。[發布run40097195424](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40097195424)成功，匿名四附件／ZIP真安裝／原profile更新與八檔hash保留通過。ZIP SHA256=d645493822e18988adb151e5eb2eb46125feadc15643f184675ab83dcf257f59；不再部署Worker。

4筆serial全有效：Codex500 Chat506/6、6.5483秒；CodexDec2787/39（cached2048）、8.4711秒；Claude500 Chat1059/103、6.2991秒；ClaudeDec1547/358、5.1472秒。第一輪16為14/16，p50=6.9945／p95=10.0236秒，受理span2.9104秒。兩筆Claude503的provider_setup為230／229ms，cli_spawn／inference均null、total236／238ms；API billing仍unknown（calls_started1/completed0），不回填零。其餘18筆完整計量／語意／profile／model／DB成本一致；已知input23429/output2223、USD0.0385174牌價等值，另2筆unknown，不當全部成本。

result transport20/20、local20/20、forward_errors0／protocol_errors0／result_delivery_retries0，傳輸失敗未重現。peak RSS2,365,008 KiB、descendants22／fd2300／running13、health p95=0.002秒。第二／三輪16及64未執行。臨時2 Key撤銷、原70 rows／所有設定／profile保留，active owner keys3。
