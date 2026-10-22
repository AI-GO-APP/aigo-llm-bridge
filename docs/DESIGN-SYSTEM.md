# 前端設計規範

設計版本：Windows 0.7.3。參考 **AI GO 合約請款管理系統**的深藍導覽／表頭、靛藍操作、暖灰淺底／深空深底、多層表面與 10／14px 圓角。這是視覺語言與互動原則的採用，不依賴 AI GO SDK、不複製其業務流程或租戶資訊。

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

`web/platform.js` 提供 browser copy／Blob CSV。Windows build 後附加 `packaging/windows/platform.js`，將兩個操作改為明確 pywebview API；`console_extension.js` 注入Windows更新卡；共用頁面不 import pythonnet／Windows SDK。無 WebView2 時開預設瀏覽器，關閉 view 不停止服務。

更改 CSS token 同時改本表；新增頁面／modal更新本檔與 ACCEPTANCE。驗收至少含淺／深色、桌面／窄版、長模型字串、空／有資料、建立KEY表單／危險確認、Windows附加卡。不可只用首頁截圖聲稱整個前端通過。Mac 需獨立重驗，不因共用CSS就宣稱已驗收。
