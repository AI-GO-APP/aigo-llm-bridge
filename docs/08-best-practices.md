# 08 · 最佳實踐

## 1. 預設用 `auto`,第一次使用就問

- 功能畫面一律 `model: "auto"`,由使用者決定優先用自己的電腦還是雲端。**不要在程式裡替使用者選**。
- 第一次使用就問(`priority_required` 是提醒,不是錯誤),設定頁隨時可改。
- 回應有 `fallback` 就顯示一句說明。使用者選了本機優先卻一直用到雲端,多半是電腦沒開;讓他知道,他才能處理。
- 只有「沒有使用者」的呼叫(排程、批次)才直接指定雲端模型。

## 2. thinking 與 effort:逐次指定,不要全域關

實測(docs/01 S1b 與平台端到端):

| 設定 | 影響 |
|---|---|
| haiku 開著 thinking(預設) | 第一段文字 12 – 23 秒,前段全是 thinking |
| haiku `reasoning: {enabled: false}` | 第一段 2.4 秒,但 JSON 格式遵守變差 |
| Opus 5.5、Fable | 關不掉 thinking,回應會列 `dropped: ["thinking_off"]` |

建議:

- **對話、即時回覆**:關 thinking(`reasoning: {"enabled": false}`)或 `reasoning_effort: "low"`。
- **要求固定格式(JSON)**:保留 thinking,並用 `response_format` 的 JSON schema。
- **分析、長文**:保留預設或提高 effort,並改用非同步。

## 3. 結構化輸出

- 用 `response_format: {type: "json_schema", json_schema: {schema: …}}`,不要只在提示裡寫「請回 JSON」。
  本機與 Anthropic 都會用結構化輸出強制;本機若模型多包了 ```json 外框,Bridge 會拿掉。
- 不要用預填(最後一則放 `assistant`):目前世代模型一律 400。

## 4. 時間上限要留餘裕

| 路徑 | 上限 | 做法 |
|---|---|---|
| Server Action 經 egress | 30 秒硬牆 | 永遠 `X-Bridge-Wait: 20`(區塊已內建),202 就回工單 id |
| Bridge 同步 | 280 秒 | 預期會超過就改用非同步 |
| 串流 | 280 秒 | 看 `complete`;`stream_timeout` 時用工單 id 取全文 |
| 本機單一工作 | 1800 秒(`AIGO_BRIDGE_JOB_TIMEOUT_S`) | 超過會失敗而不是截斷 |

## 5. 身分與權限

- 使用者身分只從平台或你自己的登入機制來(`ctx.user_id`)。**瀏覽器送來的 user id 不能信**。
- 綁定碼只能由伺服器端代表登入者產生(Bridge 也不接受 session token 產生綁定碼)。
- 一個 app 一把 source 金鑰。用量與偏好都按 source 分開,金鑰外洩時影響範圍也只有那個 app。
- 金鑰放 secrets 或環境變數,不要寫進程式碼或前端。

## 6. 本機那一側的限制要事先告訴使用者

- 只有文字與 JSON 輸出;不支援工具呼叫與圖片輸入(需要的功能請直接指定雲端模型)。
- 電腦要開著、worker 要在執行。建議請使用者裝開機常駐(docs/04 §4)。
- 用的是使用者自己的 Claude 方案額度。組織不應要求使用者用自己的方案處理別人的工作(docs/02)。

## 7. 對話延續

- 本機:帶 `X-Bridge-Session: <uuid>`,同一個 UUID 在同一台電腦上接續同一段 Claude Code 對話,
  不必每次重送完整歷史。
- 雲端:照 OpenAI 的方式在 `messages` 帶完整歷史。
- `auto` 的一段對話可能中途從本機換到雲端(例如電腦關了)。要延續上下文,**每次都送完整 `messages`**,
  同時帶 `X-Bridge-Session`;本機會接續自己的對話,雲端會用 `messages`。

## 8. 成本

- 雲端成本記在 `biz_bridge_usage.cost_usd`(`provider = openrouter`)。
- 使用者大多選本機優先時,組織的雲端帳單主要來自「電腦沒開」的備援。備援比例偏高時,
  比起加預算,先提醒使用者裝開機常駐通常更有效。
- 不要把 `BRIDGE_AUTO_CLOUD` 設成最貴的模型「以防萬一」:備援會被頻繁用到,選一個品質夠用的。
