# 05 · 呼叫端:本機 Claude Code 與 OpenRouter 並用

這份說明 app 怎麼呼叫 Bridge。核心只有一句:**用 `model: "auto"`,並在使用者第一次使用時問他要優先用哪一個。**

## 1. 選對客戶端

| 你的程式在哪裡跑 | 用什麼 | 範例 |
|---|---|---|
| Custom App 的 Server Action | [`clients/custom-app/bridge_block.py`](../clients/custom-app/bridge_block.py) 整段貼進 action | [minimal-custom-app/actions](../examples/minimal-custom-app/actions) |
| Custom App 的前端(要逐字顯示) | [`clients/browser/bridge.ts`](../clients/browser/bridge.ts) 複製到 `src/lib/` | [minimal-custom-app/src](../examples/minimal-custom-app/src) |
| Hosted App 或任何伺服器程式 | [`clients/python/aigo_bridge.py`](../clients/python/aigo_bridge.py),或任何 OpenAI 相容 SDK(§4.2) | [hosted-app-caller](../examples/hosted-app-caller) |

三者講的是同一套 API(docs/09),只是各自處理了那個環境的限制:
Server Action 連外只能走 `ctx.http.call` 而且有 30 秒硬牆;瀏覽器不能拿 source 金鑰;
伺服器程式最自由。

## 2. 每個呼叫都要帶的兩樣東西

1. **source 金鑰**:Bridge 發給這個 app 的金鑰(docs/03 §2)。只放在伺服器端:
   Custom App 放 secrets、Hosted App 放環境變數;瀏覽器改用它換來的短效 session token。
2. **使用者身分**:平台使用者 id(Server Action 的 `ctx.user_id`)。本機那一側只替使用者本人運算,
   優先順序也是依使用者存的。**身分要來自平台或你自己的登入機制,不能讓瀏覽器自己宣稱。**

金鑰與身分的完整規則見 [docs/11 §5](11-security.md)。

## 3. 優先順序與備援

### 3.1 行為

```
model: "auto"
   │
   ├─ 使用者還沒選過 ──► 409 priority_required(不套任何預設)
   │
   └─ 已選 local ──► 先試本機 Claude Code ──(沒開機、worker 失敗)──► 改用雲端
      已選 cloud ──► 先試 OpenRouter      ──(限流、5xx、金鑰問題)──► 改用本機
```

- 只有「換一個後端就可能成功」的錯誤才切換(完整清單 docs/09 §2.6)。請求本身有問題就直接回報。
- 串流只在**還沒送出任何內容**時切換,不會出現前半段是本機、後半段是雲端的回答。
- 每個回應都註明結果:`priority`(使用者選的)、`served_by`(實際回答的)、`fallback`
  (改用備援時是 `{"from", "reason"}`)。**請把 fallback 顯示給使用者看**,例如「你的電腦沒開,這次改用雲端回答」。

### 3.2 第一次使用一定要問

`auto` 在使用者選之前會回 `409 priority_required`。這是刻意的:兩個選項的代價不同
(本機用的是使用者自己的 Claude 方案額度、要電腦開著;雲端用的是組織的 OpenRouter 帳單),
這個取捨應該由使用者自己決定。

建議的做法(範例 app 就是這樣做的):

1. app 啟動時讀 `GET /bridge/preferences`。`priority` 是 `null` 就只顯示選擇卡,不顯示功能畫面。
2. 選擇卡顯示兩個選項與它們**當下**是否可用(`choices[].available`),例如「我的電腦(尚未連線)」。
   使用者仍然可以選本機優先,再去連接電腦。
3. 選好後 `PUT /bridge/preferences {"priority": "local" | "cloud"}`,進入功能畫面。
4. 設定頁放同一張卡,隨時可以改。

給使用者看的兩個選項,建議這樣描述:

| 選項 | 說明文字 |
|---|---|
| 我的電腦(Claude Code)優先 | 用你自己的 Claude 方案,在你的電腦上處理;電腦沒開時改用雲端 |
| 雲端(OpenRouter)優先 | 不需要電腦開著;雲端不可用時改用你的電腦 |

### 3.3 什麼時候不要用 `auto`

| 情況 | 改用 |
|---|---|
| 排程、批次、系統自己產生的內容(沒有使用者) | 直接指定雲端模型,例 `openrouter/anthropic/claude-sonnet-4.5` |
| 需要工具呼叫或圖片輸入 | 直接指定雲端模型(本機以無工具模式執行) |
| 使用者明確要求只用自己的電腦 | `local/self` 或 `local/self:<模型>`;沒開機就是 409 |
| 需要固定同一個模型比較結果 | 直接指定那個模型 |

### 3.4 兩個候選模型

沒帶 `models` 時用 Bridge 的 `BRIDGE_AUTO_LOCAL` / `BRIDGE_AUTO_CLOUD`。某個功能需要別的組合時,在請求帶:

```json
{"model": "auto", "models": ["local/self:sonnet", "openrouter/anthropic/claude-sonnet-4.5"], "messages": [...]}
```

各放一個本機與一個雲端,順序不影響(順序由使用者的優先決定)。

## 4. Hosted App 與伺服器程式

### 4.1 Python 客戶端

```python
from aigo_bridge import BridgeClient, Pending

bridge = BridgeClient(os.environ["BRIDGE_URL"], key=os.environ["BRIDGE_KEY"])

view = bridge.get_priority(user_id)
if view["priority"] is None:
    ...  # 回給前端,讓使用者選;選好後 bridge.set_priority(user_id, "local" | "cloud")

reply = bridge.chat([{"role": "user", "content": question}], user=user_id, wait=60)
if isinstance(reply, Pending):                 # 超過 wait 秒:工作還在跑
    reply = bridge.wait_job(reply.job_id, user=user_id)
print(reply.content, reply.served_by, reply.fallback)

for event in bridge.stream(messages, user=user_id):
    if event.kind == "delta":
        send_to_client(event.text)
    elif event.kind == "done" and not event.complete:
        ...  # 內容不完整(串流上限或中途失敗),見 docs/06 §3
```

要讓金鑰不出現在請求裡,加 `source="SALES_APP"` 改用 HMAC 簽章。錯誤一律是 `BridgeError`,
`code` 是穩定的代碼(docs/09 §7)。

### 4.2 OpenAI 相容 SDK

Bridge 講 OpenAI 的線路,所以既有的 SDK 只要換 base URL、金鑰,再加一個使用者標頭:

```python
from openai import OpenAI

llm = OpenAI(base_url=os.environ["BRIDGE_URL"] + "/v1", api_key=os.environ["BRIDGE_KEY"],
             default_headers={"X-Bridge-User": user_id})
resp = llm.chat.completions.create(model="auto", messages=[{"role": "user", "content": "你好"}])
meta = (resp.model_extra or {}).get("x_bridge")    # served_by、priority、fallback
```

`priority_required` 會以 SDK 的 409 例外出現(`openai.ConflictError`),`e.body["code"]` 可以判斷。
每位使用者一個 client,或每次呼叫用 `extra_headers={"X-Bridge-User": user_id}`。

## 5. Custom App 的 Server Action

把 [`bridge_block.py`](../clients/custom-app/bridge_block.py) 從「從這裡開始貼」到「到此為止」整段貼進 action,然後:

```python
def execute(ctx):
    res = bridge_chat(ctx, ctx.params.get("messages") or [])
    if not res["ok"] and res["code"] == "priority_required":
        ...                                   # 回給前端:請使用者選(bridge_set_priority)
    elif res.get("pending"):
        ...                                   # 20 秒內沒做完:把 job_id 回給前端,之後用 bridge_job 查
    ctx.response.json(res)
```

- **slug 必須寫死在程式碼裡**(區塊裡的 `"llm-bridge"`)。發布閘門只認得字面字串。
- 區塊每次都帶 `X-Bridge-Wait: 20`。egress 閘道的硬牆是 30 秒,撞牆時整支 action 可能被砍,
  而且有兩種不同的失敗形狀(docs/01 S3)。
- 回應的中繼資訊讀本體的 `x_bridge`。`ctx.http.call` 拿不到回應標頭。
- manifest 的 `timeout_ms` 設 35000 左右;設更長沒有用,牆在 egress 那一層。

## 6. Custom App 的前端

要逐字顯示就從瀏覽器直連 Bridge 串流,見 [06 · 前端串流](06-frontend-streaming.md)。
簡短版:`streamChat({messages}, onDelta)`,結果看 `complete`、`fallback`、`error.code`。

## 7. 同步、非同步、串流怎麼選

| 情況 | 用 | 注意 |
|---|---|---|
| 要逐字顯示 | 串流 | 上限 280 秒;看 `complete` 判斷完整 |
| 伺服器端要拿結果接著處理,預期很快 | 同步 | Server Action 用 `wait=20`;其他用 `wait` ≤ 280 |
| 可能很久(長文、深度思考) | 非同步 `X-Bridge-Async: true`,或同步等到 202 再輪詢工單 | 工單結果要由**同一位使用者**查 |
| 排程或批次 | 指定雲端模型 + 非同步 | 本機需要使用者的電腦開著,不適合無人值守 |
