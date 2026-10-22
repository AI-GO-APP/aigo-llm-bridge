# Windows 0.7.1 WebView2 驗收

本輪以 API／CLI 與應用程式自己的隱藏 WebView2 renderer 驗證，沒有 Computer Use、桌面輸入或供應商 CLI 登入操作。未變更 Mac 或 Cloud。公開發布及正式安裝結果由完成後的 release 紀錄另行確認。

## 隔離驗收

Windows 11 x64、Python 3.14.3、pywebview 6.2.1、pythonnet 3.2.1；鎖定依賴見 packaging/windows/requirements-lock.txt。獨立 LocalProbe package／profile／loopback 更新站，A=0.7.0、B=0.7.1。

`tools/verify_installer_update.py` 的 `.desktop-build/webview-native-acceptance-3/acceptance.json`：39／39 通過。這是實際 Setup／Velopack 更新；該輪 source 為工作樹，CI 另從提交版本重跑相同閘門。

| 項目 | 結果 |
|---|---|
| 真正 frozen WebView2 renderer 與 Windows 適配層 | 通過；不附 Chromium |
| 新 KEY 的前端預設、管理 API 省略 providers | Claude／Codex 全開 |
| 前端複製按鈕→原生剪貼簿→讀回 | 精確相同；同 KEY 真 HTTP models 認證兩來源 |
| CSV 前端事件→原生 bridge→管理 API→檔案 | 欄位等於 LOG_COLUMNS、合成 token／cost 存在、無 KEY |
| 瀏覽器共用前端、取消匯出與缺少 WebView2 備援 | 適配層及單元測試通過 |
| 關閉管理視窗 | 相同 KEY 的背景 HTTP 服務仍可使用 |
| 開著隱藏管理視窗執行真 A→B 更新 | 視窗正常退出、新版背景服務啟動 |
| URL、device_id、既有 KEY hash、DPAPI、token／cost、接單狀態 | 更新後保留 |
| 壞簽章／feed、忙碌排空逾時、最低版本限制及重啟 | 拒絕不安全更新或保留限制 |
| 解除安裝及測試 KEY | 保留 profile、撤銷測試 KEY |

封裝版最初兩輪在組合 evaluate_js 的複製測試期間以原生 heap 錯誤退出；把呈現、事件與讀取分成獨立步驟後，固定 renderer 驗收連續五輪通過，再完成上述完整 39 項。故障僅發生於隔離測試；不將最初失敗包發布，也不宣稱已定位所有上游原生原因。

## API／CLI 驗收界線

CSV 測試以固定測試檔案路徑代替 Save 對話框的選擇結果，之後的真實 API 與寫檔均執行。尚未人工驗收系統儲存對話框的點選／取消、視窗視覺排版與使用者桌面前景切換。隱藏視窗的關閉及更新生命週期已實測；不把它描述為人工關窗驗收。

新 KEY 全開指所有受支援來源中目前及未來已登錄模型，仍受本機目錄、CLI 訂閱及參數相容性限制；既有 KEY 不擴權，輪替沿用原 scope。不新增外網推論或供應商登入測試，本輪亦不重佈署 Worker。


## 公開 HTTPS 更新補正：0.7.2

0.7.1 公開包的匿名下載、實際 Setup、重啟與資料保留 18／18 通過。正式接管 0.6.3→0.7.0 後，才發現 GitHub 上的原生 apply 回 404；原先的 loopback A→B 不會觸發此 SDK 行為。錯誤發生在排空／停止前，接管後的服務已恢復原接單狀態，既有 KEY 與資料保留。

Velopack 把 github.com 的字串來源自動當作 GithubSource，無法代表固定 Release 目錄。以官方 `HttpSource` 明確讀取同一真 HTTPS feed，已成功取得目標 0.7.1；0.7.2 修正呼叫並加入使用實際 SDK source 類別的回歸保護。同時固定 Windows 發布工具 subprocess 的 UTF-8 解碼。142 passed、2 skipped，Node 9 passed。已發布 0.7.1 產物保持不可變；0.7.0／0.7.1 需要一次 Setup 或受控簽章修復流程，不能宣稱舊客戶端自行更新成功。正式最終版本及公開 HTTPS 套用結果記在 Release 驗收紀錄。


0.7.2 回歸另發現「視窗事件已釋放，但程序仍在結束」的競爭；Velopack log 明確記錄強制終止該 viewer PID。更新現在會核對本設定檔 viewer 的 PID 及精確執行檔，等待 OS 程序退出後才套用，並等待自有 watcher 結束；不終止其他設定檔或供應商程序。驗收同時要求視窗收據為 closed 且退出碼為 0，不能只用事件釋放或更新成功判定關窗通過。


## 0.7.2 後續實際桌面補充

使用已發布0.7.2執行檔與獨立profile，透過Computer Use完成原生Save／中文檔名／Cancel、KEY建立表單兩來源預選及主要頁面閱讀。合成CSV回讀欄位等於LOG_COLUMNS、1筆、輸入17／輸出9 tokens、0.012345 USD；取消後CSV仍只有1檔。按右上X後視窗消失、同profile背景API health為HTTP200。沒有建立正式KEY或改啟動設定。

預設瀏覽器備援CLI退出0、狀態mode=browser，且出現「總覽 · LLM Bridge」Chrome視窗；Computer Use因無法可靠辨識瀏覽器URL而自動停止，未取得該瀏覽器畫面的可信確認，故此部分仍只記啟動成功，非視覺通過。先前原生copy→OS剪貼簿為隱藏frozen WebView實測，不能描述成人工按copy已驗收。
