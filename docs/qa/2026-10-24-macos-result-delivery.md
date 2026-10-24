# Mac 0.9.14：已計算結果交付

2026-10-24，R-27／D-47，refs #39／#46。候選0.9.14尚未合併、發布或正式安裝。原機目前已回復0.9.12-mac.1、Worker0.9.5-relay，4＋4／64／64保留；0.9.13驗收失敗的[完整收據](2026-10-24-macos-relay-batch-release.md)及immutable附件保留，不重新送出失敗推論。

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
