# Windows 0.7.3 設計與文件驗收

範圍：Windows視覺更新與repo文件體系。採深藍／靛藍合約請款視覺語言、系統深淺色、六頁與Windows更新卡；不修改供應商登入、不部署Worker、不發布Mac。版本與資料分離；沒有DB schema變更。

## 驗收紀錄

本檔在工作開始先建立。以下結果須完成實測後更新，不能以規格代替證據。

| 閘門 | 本輪狀態 |
|---|---|
| 文件覆蓋／連結、隨包文件 | schema／settings／API／tokens及連結檢查通過；核心文件已在真native建置stage隨包 |
| Python／Node／terms／secret檢查 | 147 Python passed、2 skipped；Node relay 7＋platform 2 passed；22字詞及secret掃描通過 |
| 六頁淺深色與窄版render、modal、Windows卡 | 1440×1000及390×844，淺／深色×六頁24組均無整頁橫向溢出；建立KEY modal四組尺寸／主題皆完整、兩來源預選；輪替取消、空篩選、成本欄及keyboard focus通過；無console error |
| 隔離Setup→A→B、native copy／CSV／關窗 | 39／39通過；來源ede4c1a乾淨commit，A=0.7.0／B=0.7.1為測試包號，皆包含本輪新UI；KEY／URL／metadata／DPAPI保留，測試KEY已撤銷 |
| PR／CI／公開Windows release | PR #14已squash合併d3f2707；一般CI、舊ZIP、原生runner及publish全通過；0.7.3已發布 |
| 正式Windows更新與URL／KEY／資料保留 | 標準0.7.2→0.7.3更新＋重啟，21項本機檢查通過；Worker既有外網故障另列 |

Mac新UI未驗收，瀏覽器／WebView共享前端不代表Mac原生殼驗收通過。所有驗證使用合成profile／內容；公開報告不含完整KEY、管理URL fragment或個人資料。


## 視覺證據與範圍

以下為實際內建瀏覽器render，獨立合成profile，沒有CLI推論或Cloud部署；Windows更新卡由實際console_extension注入，版本標記source-preview，不能代替frozen安裝證據。完整24組尺寸收據與截圖保留於本機忽略的design-visual證據目錄。

![淺色總覽](assets/windows-0.7.3-overview-light.png)

![深色設定與Windows更新卡](assets/windows-0.7.3-settings-dark.png)

主要前景對比實測：淺色內文19.17、說明5.53、操作文字5.75；深色16.24／7.96／8.80；主按鈕白字4.70、深藍表頭白字11.25。上述達4.5:1目標，不宣稱完整WCAG認證。鍵盤Tab移至下一導覽時有solid outline。空篩選可見明確說明，成本0.012345正確顯示。

本機tools測試47項通過，既有Mac shell gate因Windows選到未安裝的WSL而失敗；同PR Ubuntu CI docs job已通過全部工具測試，未修改Mac程式。Windows版本閘門另補文件PNG分類與防止程式檔繞過案例，7項針對性回歸通過。


## 已發布與正式已安裝

[PR #14](https://github.com/AI-GO-APP/aigo-llm-bridge/pull/14)已合併，程式來源 `d3f27071dac72350635ff4a938afa9cfd751624c`。以下CI均成功：[一般CI](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39875835997)、[Windows舊ZIP與文件](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39875835908)、[原生runner](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39875835920)、[正式package／announce](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39876542892)。[Windows 0.7.3 Release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases/tag/windows-installer-internal-v0.7.3)已公開。沿用原更新公鑰，policy sequence=4、minimum_version=0.7.0；仍無Authenticode。

| 產物 | 大小／SHA256 |
|---|---|
| Setup | 40,326,215 bytes；`d953390ba791db59597fbac01e32d8af28a55f50f8a899793a6774c744160f87` |
| full nupkg | 32,812,103 bytes；`cc390ef6f89192b8184c4036b94d01399e48465ece90acc005298bc19be2c130` |

正式原安裝使用0.7.2自己的CLI，經公開GitHub HTTPS與官方Velopack更新為0.7.3，再正常停止／重啟一次。**21項本機交付檢查通過**：

- 同一RAM測試KEY於更新前、更新後、重啟後均能本機GET models，新KEY預設兩來源全開。
- 保留device_id、固定URL、models／default_model、Cloudflare帳戶／Worker綁定、所有既有KEY列、183筆request metadata及cost、原DPAPI bytes、自動啟動及接單狀態。
- SQLite quick_check為ok；CSV欄位等於LOG_COLUMNS且沒有完整KEY。
- 安裝的GUI／CLI／CSS／SCHEMA／文件入口與公開nupkg逐項bytes hash相同，七份產品規格已隨包安裝。
- 測試KEY全部撤銷，原KEY未輪替或擴權；沒有新的供應商推論、沒有操作供應商登入，沒有改Cloud設定或Mac發布。

原KEY基準為27筆；第一次外網測試新增的臨時KEY已撤銷，第二次本機更新因此比較28筆既有列（含該已撤銷測試列）。原有27筆均逐列保留，不是重建KEY冒充保留。只在本機忽略目錄保存metadata備份與完整21項布林收據，公開報告不含endpoint、KEY或配對資料。

## 外網未通過：更新前已有的Worker問題

第一次驗收在**仍為正式0.7.2、尚未套用更新**時就失敗：Relay為離線／重連中。直接路徑health 403；使用與產品相同的網路及certifi TLS設定後，Cloudflare回HTTP500、plain text error code 1101。該次測試KEY已撤銷，未套用任何更新。

完成Windows本機更新與重啟後，以相同TLS驗證設定回讀同一Worker，仍為HTTP500／1101。因此 **Worker外網LLM呼叫未通過**；不能把GitHub HTTPS更新成功當成Worker HTTPS推論成功。依工作範圍未重部署Worker、未修復Cloud／secret、未介入Mac。Windows程式、本機API及資料保留已驗收；Worker故障須在Cloud維護範圍另處理。

## 純文件更新閘門

純Markdown及指定QA圖片收據不強迫核心／Mac升版，程式仍受原版本閘門保護。實際Git Bash執行CI插入片段：Markdown／QA圖片可略過，runtime程式及偽裝為asset的.py不可略過，4情境通過。本次後補收據不重建或替換0.7.3發布產物，安裝內文件保持其build commit快照，repo保存最新交付狀態。
