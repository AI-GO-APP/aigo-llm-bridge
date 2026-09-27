# 06 · Custom App 前端:直連串流

Custom App 的前端可以不經 Server Action、直接從瀏覽器連 Bridge 串流,逐字顯示回答。
客戶端是 [`clients/browser/bridge.ts`](../clients/browser/bridge.ts),整檔複製到 `src/lib/bridge.ts`。

## 1. 為什麼可以直連、為什麼要這樣做

- Custom App 執行頁的 CSP 是 `connect-src 'self' https://ai-go.app https://*.ai-go.app`。
  Bridge 部署成 Hosted App 後網址是 `*.deploy.ai-go.app`,在允許範圍內。**所以 Bridge 不能綁自訂網域。**
- 經 Server Action 轉一手的話,每次呼叫都有 30 秒硬牆,也沒辦法串流。
- 瀏覽器不能拿 source 金鑰。做法是由 Server Action `bridge_session` 用 source 金鑰換一張綁定登入者的短效
  token(最長 1 小時),`bridge.ts` 會快取並在快到期時自動換新。

## 2. 最小用法

```tsx
import { streamChat, getPriority, setPriority } from "../lib/bridge";

const res = await streamChat(
  { messages: [{ role: "user", content: prompt }] },   // model 預設 "auto"
  (textSoFar) => setOutput(textSoFar),
  { conversation },                                     // 選填:同一個 UUID 可延續本機對話
);
if (res.error?.code === "priority_required") showPriorityChooser();
else if (!res.complete) showIncomplete(res.error);
if (res.fallback) showNote(`這次改用備援(${res.fallback.from} 不可用)`);
```

`StreamResult` 的欄位:`text`、`complete`、`error`、`servedBy`、`dropped`、`priority`、`fallback`、
`firstTokenMs`、`totalMs`。

## 3. 怎麼判斷回答完整

**只看一件事:收到 `[DONE]` 而且之前沒有 `error` 事件**(`res.complete`)。

| 情況 | 你會看到 | 處理 |
|---|---|---|
| 正常結束 | `complete: true` | — |
| 串流到 280 秒上限 | `complete: false`、`error.code = "stream_timeout"`、`error.job_id` | 工作仍在進行。稍後用 `getJob(job_id)` 取全文 |
| 中途失敗(電腦斷線、上游錯誤) | `complete: false`、`error.code` 是那個原因 | 顯示原因;可以重送 |
| 連線被平台直接切斷 | `complete: false`、沒有 `error` | 平台 300 秒上限或網路中斷;Bridge 會在 280 秒先收尾,正常不會發生 |

不要用「連線結束」判斷完整:Hosted App 單一請求 300 秒一到會直接斷線,**不會**給錯誤狀態碼。

## 4. 第一次使用:先問優先順序

`model: "auto"` 在使用者選之前會被拒絕(`priority_required`)。範例 app 用一個關卡元件
[`PriorityChooser`](../examples/minimal-custom-app/src/components/PriorityChooser.tsx):

- `gate` 模式包住功能頁:還沒選就只顯示選擇卡。
- 一般模式放在設定頁:隨時可以改。
- 每個選項顯示當下是否可用(`choices[].available`),例如「電腦尚未連線」,但不擋使用者選。

## 5. 錯誤代碼對應的畫面文字

| `error.code` | 建議顯示 |
|---|---|
| `priority_required` | 顯示選擇卡(不是錯誤訊息) |
| `no_worker_for_user` | 「你的電腦目前沒有連線。請到『連接我的電腦』確認 worker 正在執行。」 |
| `stream_timeout` | 「回答較長,已轉到背景完成。」並提供「取得完整內容」按鈕 |
| `provider_rate_limited` | 「雲端服務忙碌中,請稍後再試。」 |
| `provider_auth`、`provider_billing` | 「雲端服務設定有問題,請聯絡管理者。」(不是使用者的錯) |
| `bad_local_model`、`bad_auto_models` | 開發階段的錯誤:model 寫法不對 |
| 其他 | 直接顯示 `error.message`(Bridge 的訊息都是給人看的句子) |

## 6. 注意事項

- **畫面在 Shadow DOM 裡**:`confirm()` / `alert()` 不能用;自動化測試要用 `data-testid` 找元素。
- **背景分頁會被瀏覽器節流計時器**:在背景分頁量到的前端時間(第一段幾毫秒)不準。
  串流本身不受影響,但別拿背景分頁的數字當效能依據。
- **thinking 會讓第一段變慢**:本機優先時,Bridge 要等第一段內容(或失敗)才回應標頭。
  開著 thinking 的模型,第一段可能要十幾秒;對話型畫面可以逐次帶 `reasoning: {enabled: false}`(docs/08 §2)。
- **取消**:`streamChat(body, onDelta, { signal })` 帶 `AbortController.signal`;
  取消後本機那一側的工作仍會做完(結果留在工單上)。
