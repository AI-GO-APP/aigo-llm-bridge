# minimal-custom-app:接上 Bridge 的最小 Custom App

三個畫面,涵蓋 Custom App 會用到的全部接法:

| 畫面 | 做什麼 | 用到 |
|---|---|---|
| 第一次打開:選優先順序 | 「我的電腦(Claude Code)」或「雲端(OpenRouter)」擇一優先,沒選不能用 | `PriorityChooser`(gate 模式) |
| 對話 | 瀏覽器直連串流;模型、effort、thinking 逐次指定;顯示實際由誰回答、有沒有用到備援;另有「從伺服器端送出」 | `streamChat`、`bridge_chat` action |
| 連接我的電腦 | 改優先順序、產生綁定碼、列出與撤銷自己的電腦 | `bridge_computers` action |

這個範例在 AI GO 平台上實際發布並驗證過(結果見 docs/01 §5):前一版以瀏覽器操作逐項驗證;加入優先順序的這一版以 action 與瀏覽器用的 session token 走真實路徑驗證,畫面點擊留待下一次瀏覽器驗證。

## 檔案

以平台的 `starter-internal` 起手式建立,**這裡只放要覆蓋或新增的檔案**;其餘(版面元件、`App.css`、
`main.tsx`、平台 SDK)沿用起手式。

| 檔案 | 作用 |
|---|---|
| `actions/bridge_session.py` | 用 source 金鑰換短效 session token(綁 `ctx.user_id`),前端拿去直連 Bridge |
| `actions/bridge_computers.py` | 產生綁定碼、列出與撤銷「我的電腦」 |
| `actions/bridge_chat.py` | 伺服器端同步呼叫(`X-Bridge-Wait: 20`,超過回工單 id,`op=job` 查) |
| `actions/bridge_priority.py` | 伺服器端讀/設優先順序(前端也可以直接用 session token 呼叫 Bridge) |
| `actions/manifest.json` | 四支 action 的逾時設定 |
| `src/lib/bridge.ts` | 前端客戶端(`clients/browser/bridge.ts` 的副本) |
| `src/components/PriorityChooser.tsx` | 優先順序選擇卡,`gate` 模式包住功能頁 |
| `src/pages/ChatPage.tsx`、`ConnectPage.tsx` | 兩個頁面 |
| `src/App.tsx`、`src/routes.ts`、`src/pages/_manifest.json` | 路由與側邊選單 |

四支 action 開頭都貼了同一段 `clients/custom-app/bridge_block.py`(「從這裡開始貼」到「到此為止」),
每支 action 自己只有幾行。改區塊請改正本再跑 `python tools/sync_clients.py`。

## 建立步驟

先完成 [docs/03](../../docs/03-deploy-bridge.md) 部署好 Bridge,並替這個 app 產生一把 source 金鑰
(例 `BRIDGE_KEY__MY_APP`,Bridge 端要設好)。

1. **建 app**:Builder 用「內部應用(starter-internal)」起手式建一個 Custom App。
2. **刪起手式的示範檔**:`_template.json`、`actions/summarize_leads.py`、`actions/export_leads_csv.py`、
   `src/pages/DashboardPage.tsx`、`src/pages/ListPage.tsx`。
   `_template.json` 宣告了用不到的外部服務,不刪發布會被擋。
3. **放入這個資料夾的檔案**(覆蓋同名檔)。
4. **外部服務**:Builder「外部服務」新增 slug **`llm-bridge`**,base_url = Bridge 網址
   (`https://<your-bridge>.deploy.ai-go.app`),逾時 30000 毫秒,並授權給這個 app。
   slug 若要取別的名字,四支 action 裡區塊的 `"llm-bridge"` 字串都要一起改(發布閘門只認字面字串)。
5. **secrets**:`BRIDGE_KEY` = 那把 source 金鑰的值;`BRIDGE_PUBLIC_URL` = Bridge 網址。
6. **編譯、發布**。剛發布後第一次呼叫 action 可能回 503(冷啟動),稍等再試。

用 API 做 4、5 兩步的端點見 docs/03 §6。

## 驗證清單

| 步驟 | 預期 |
|---|---|
| 第一次打開 | 只看到「開始之前:你想優先用哪一個?」 |
| 選「雲端」 | 進入對話頁;送出後由 OpenRouter 回答,實際型號顯示雲端模型 |
| 改選「我的電腦」,電腦還沒連 | 送出後仍會回答,並顯示「已改用備援(local/self 不可用:no_worker_for_user)」 |
| 連接我的電腦 → 產生綁定碼 → 在電腦上 `enroll`、`run` | 清單顯示「在線」 |
| 再送出 | 實際型號顯示 `local:<型號>`,沒有備援說明 |
| 從伺服器端送出一個長題目 | 20 秒時回 `pending` 與 `job_id` |
| 撤銷電腦 | worker 自行結束;之後送出改用雲端 |

## 兩條呼叫路徑怎麼選

| 情境 | 走法 | 上限 |
|---|---|---|
| 要逐字顯示給使用者看 | 前端 `streamChat()` 直連 | 280 秒後 Bridge 主動收尾並送 `stream_timeout` 與工單 id |
| action 裡要拿結果接著處理 | `bridge_chat` | egress 閘道 30 秒硬牆;20 秒沒做完回 `pending`,用 `op="job"` 查 |

串流是否完整只看一件事:收到 `[DONE]` 且之前沒有 `error` 事件。連線被平台切斷時不會有錯誤狀態碼。
