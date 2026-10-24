# 前端設計規範

串接頁的公開入口狀態卡沿用現有 card／button／muted／test-privacy tokens，分列本機支援、Worker 版本、裝置在線、路由檢查時間及各模型／協定的推論證據。unchecked／過期、404 待更新、route reachable、推論通過分開呈現；檢查按鈕不推論，Chat／Decisions 測試由明確協定選項觸發。舊 Worker 的 unsupported 範例不可複製；未知狀態範例與 handoff 明示待驗。窄版沿用單欄與現有表單捲動，不新增頁面或平台依賴。

設計版本：Local Token Buffet Bridge。使用深藍導覽／表頭、靛藍操作、暖灰淺底／深空深底、多層表面與 10／14px 圓角；設計 tokens 與互動原則由本專案獨立維護。

實作正本：[style.css](../desktop_bridge/web/style.css)、[index.html](../desktop_bridge/web/index.html)。保留 LLM Bridge 產品識別；不把它包裝成合約系統。Windows／browser 共用同一份 DOM／CSS，平台檔只適配原生功能。

## Tokens

| Token | 淺色／深色或用途 |
|---|---|
| --page | #f9f9f7／#050506 頁面底色 |
| --surface | #fcfcfb／#101014 卡片與頂欄 |
| --surface-solid | #ffffff／#15151b 表單與 modal |
| --surface-hover | #f1f1ee／#1d1e27 輸入群組與 hover |
| --ink | #0b0b0b／#ededef 標題／主要文字 |
| --ink-2 | #52514e／#b4b7c0 內文與標籤 |
| --muted | #686760／#a4a8b0 說明；比參考系統提高小字可讀性 |
| --border、--grid | 低對比細邊界／網格基礎；不以粗框區分所有層級 |
| --accent | #4d59c6／#a2aaff 文字操作與焦點；深底提高前景亮度 |
| --accent-bright、--accent-ink | #5e6ad2、#ffffff 主按鈕固定底色／文字 |
| --accent-bg | 半透明靛藍提示與 hover |
| --good、--good-bg | 綠色文字／底，表示成功或就緒，不作品牌主色 |
| --warning、--warning-bg | 琥珀文字／底，暫停、排隊或警告 |
| --danger、--danger-bg | 紅色文字／底，失敗、撤銷等危險操作 |
| --nav-bg、--nav-bg-2 | #003685、#0047ab，兩種主題均固定深藍漸層 |
| --nav-ink、--nav-muted | 白字／半透明白說明 |
| --nav-border、--nav-hover、--nav-active | 半透明白的邊界、hover、選中背景 |
| --thead-bg、--thead-ink | #003685／#ffffff，兩種主題均固定 |
| --shadow-sm、--shadow、--shadow-lg | 控制／卡片／modal 三層陰影 |
| --ambient | 淺色 transparent；深色低強度靛藍環境光 |
| --radius、--radius-lg | 10px 卡片、14px modal |
| --ease-out | cubic-bezier(.16,1,.3,1)，互動一致 |
| --mono | Consolas／SFMono-Regular／monospace，模型／金額／範例 |

淺／深色跟隨 `prefers-color-scheme`，原生表單 `color-scheme: light dark`。不保存 theme secret 或加入遠端 theme 依賴。要新增第三套主題須另立決策，不能隨頁面硬編顏色。

## 版面與字體

- 側欄 216px；≤1120px 縮為202px。主區最大1530px，桌面 padding32px，大桌面44px。
- 系統字型 Inter 優先但不下載；Segoe UI／Microsoft JhengHei UI／系統 fallback。內文13–14px、表格12px、標題26px。小字至少10px，核心操作至少12px。
- 4張統計卡；≤880px 為2欄。≤1120px 總覽主要卡片改單欄；≤620px 導覽變3欄×2列，表單／工具列折行。
- 卡片不溢出 grid；模型名稱、endpoint與程式碼有明確裁切／捲動容器。寬表在 `.table-wrap` 水平捲動，整頁不橫向溢出。不得為塞入窄版而把數字縮成不可讀小字。

## 六個頁面

| 頁面 | 結構與必要狀態 |
|---|---|
| 總覽 | 簡潔標題＋接入操作、四個統計、入口／訂閱卡、最近請求、暫停／恢復。KEY數、CLI登入與Worker在線分開，不把登入等同訂閱可用性。 |
| 串接指南 | endpoint→模型→明確需額度的測試→範例；測試 KEY 不保存並清空，不能自動執行測試。 |
| API金鑰 | 提示只顯示一次、服務表、建立／輪替／撤銷 modal；新建兩來源預選，輪替不擴權。完整 KEY 只在一次性 modal，關閉清空 DOM。 |
| 請求紀錄 | 狀態／來源篩選、CSV、清除確認、metadata表。含 token、牌價估值USD，不顯示原始內容；未知 cost 顯示破折號。 |
| 模型管理 | 可編輯映射列；id／provider／native與刪除；說明保存預設模型的實際規則，不誤稱第一列永遠預設。 |
| 連線與設定 | 設定敘述／欄位兩欄卡；窄版單欄。Windows update 卡採相同結構，清楚分 Windows 安裝版本與共用核心版本。 |

## 互動與可及性

active 導覽有白色邊線及 aria-current；狀態同時有文字，不只靠顏色。所有互動有可見 keyboard focus；主要按鈕約42px高，導覽≥44px。reduced-motion 關閉過場。native dialog 可 Escape／取消；危險操作用明確確認 modal，取消不得寫入。

loading、空清單、離線上次資料、錯誤、成功、disabled、required update 必須有文字狀態。離線不能繼續顯示為成功連線。錯誤不回顯機密／原始 CLI event。主要文字對比以 WCAG AA 4.5:1 為目標；實測結果記在驗收文件，不把設計目標直接宣稱通過。

## 平台適配與維護

Mac `web/macos.js`／`macos-onboarding.js` 使用同一六頁 tokens 與 dialog 樣式；僅注入 Mac 設定卡、五步精靈及 WKWebView clipboard／Save 適配。AC sleep 與 macOS 系統授權有明確同意按鈕，不預勾；視覺與生命週期依 [Mac QA](qa/2026-10-23-macos-parity.md) 獨立記錄。

`web/platform.js` 提供 browser copy／Blob CSV。Windows build 後附加 `packaging/windows/platform.js`，將兩個操作改為明確 pywebview API；`console_extension.js` 注入Windows更新卡；共用頁面不 import pythonnet／Windows SDK。無 WebView2 時開預設瀏覽器，關閉 view 不停止服務。

更改 CSS token 同時改本表；新增頁面／modal更新本檔與 ACCEPTANCE。驗收至少含淺／深色、桌面／窄版、長模型字串、空／有資料、建立KEY表單／危險確認、Windows附加卡。不可只用首頁截圖聲稱整個前端通過。Mac 需獨立重驗，不因共用CSS就宣稱已驗收。

0.8.0 候選 `packaging/windows/onboarding.js` 是 Windows 專用五步安裝 dialog：沿用既有 tokens／按鈕／表單／深淺色，最大寬 960px、最大高 92dvh、內容捲動。首次未完成時不能按 Esc／× 誤關，但可明確按暫存進度進主畫面調整模型／CLI；完成旗標不變，設定卡顯示尚未完成，下次啟動繼續。也可關閉整個管理視窗；完成後日常不彈出。不得預勾電源風險同意／帳戶部署授權，不以 busy 卡住背景管理；KEY 只留密碼輸入框 RAM，關閉清空。電源 UAC、OAuth、訂閱額度測試皆需明確按鈕，狀態有失敗及未驗說明。五步、權限取消、淺深色及窄版需另驗，見 [ONBOARDING](ONBOARDING.md)。

Mac 安裝與更新卡顯示來源版本／commit、精靈狀態與排空更新；發布後文字明確引導 GitHub Release source ZIP 與手動來源更新，不再顯示「沒有公開安裝包」。不把來源更新按鈕說成自動下載或 Windows 簽章更新。

0.9.9 的「常駐與併發」沿用 settings-card／field-grid，為獨立 form，不把容量變更混入一般設定或模型儲存。三欄整數、明示大小關係與常駐 0；接單中／仍有工作時停用套用，server 再獨立驗證。Windows 常駐欄停用並說明未開放，執行與受理容量仍可設定；狀態文字含有效配置與 idle／starting／active／closing。深淺色、窄版與 Windows 附加卡另驗。
