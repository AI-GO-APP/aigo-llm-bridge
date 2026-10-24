# Mac 0.9.16：4＋4常駐／共用32限定交付

2026-10-24，R-29／D-49，refs #39／#46／#60。owner明確同意保留LLM／Decisions各4個Codex常駐，執行與總受理兩者均32（所有API／provider合計），只需簡易驗證、不做併發或高token驗證，可直接合併發布／更新，失敗留紀錄回復。本文件分開記操作／發布／本機簡易驗收，不把未做的真32穩定度寫成通過。

## 發布邊界

0.9.16延續main已合併的0.9.15 runtime，沒有新的推論／Relay實作改動；版本常數與文件交付owner指定配置，沿用既有容量工具。0.9.13–15的失敗未被覆蓋，poll缺確認與外部交付／資源風險仍追蹤#60，Claude cold、Decisions StructuredOutput／thinking／schema保留。其他安裝者預設64／常駐0、Windows發布與設定不受此profile操作影響。

本機Runtime以共享名額限制驗證＋排隊＋執行32，不是每API各32。Worker0.9.5既有relay層最大pending64與health常數未改；其轉送到Runtime後超過本機32會被拒絕429。不能把這次設定宣稱成Worker入口本身已改32；本輪不部署Worker。

## 限定驗收與回復

僅使用health／models／四類preflight（兩provider×LLM／Decisions，逐筆）與設定／原生安裝啟停：零模型推論，不呼叫probe或completion／decisions推論POST，不執行原機真API併發／負載；既有離線CI／單元回歸只用fake runner，不呼叫訂閱。測試Key只在RAM，最後撤銷；API raw內容與credential不落盤，僅allowlist metadata。既有request DB列數與CLI呼叫／用量不得因驗收增加。

先在原0.9.12透過mac_service workers原子套用8／32／32並驗8idle、profile各4、接單且無queued/running；容量失敗回原8／64／64。再從公開0.9.16 ZIP更新同profile；程式更新失敗依update回復原0.9.12並保留已確認32配置。保留原URL／device／owner Key rows／模型／個人CLI config；不改登入、電源或鎖定。公開下載／hash／真ZIP安裝、CI與原安裝更新實際結果待補，沒有先宣稱已發布。

本機維護回歸：Bridge366 passed／18平台限定skip，Worker17 passed；產品文件／branding／version／secret scan／diff通過。故意斷線fixture有loopback ConnectionResetError診斷但suite全過，不當正式網路故障。本機lint_terms --require因缺私有清單明確拒絕，仍要求repo CI帶secret的require檢查通過才合併。原0.9.12已原子套用8／32／32，profile idle各4、接單且無queued/running；75既有Key rows與所有其他settings保留，request DB列數未增加，0模型推論。
