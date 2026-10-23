# 給其他電腦的 AI IDE / Web IDE

管理台「公開入口狀態」分開顯示本機版本、Worker 路由及真實推論證據。先按「檢查公開路由」（不傳 Key、不推論）；若新路徑 404，在原帳戶更新同一 Worker。route reachable 仍須用你的服務 Key 分別測試 Chat／Decisions；驗證時間、模型及成本僅留本次程序 RAM。複製的訊息帶入已知狀態，CLI 無證據時明示未驗；不得將本機支援清單當成公開路由已部署。

完成自己的 BYO 部署後，在本機管理台建立長效 API key，按「複製給 AI IDE（含金鑰）」；只在該 key 的一次性視窗提供。關閉後無法查回明文。日後可在「串接指南」複製不含 key 的標準說明，再分別設定呼叫端的 secret。CLI 對應為 `key-create --providers codex --label 'My service' --handoff`；只輸出一次，不能另存為 repo 檔案。要重新取得非秘密說明用 `handoff --providers codex`。

標準訊息會帶入真實的 Base URL、GET models、POST chat/completions、模型、環境變數名稱、最小 JSON、timeout／重試設定、usage.cost 語意與不支援的參數。帶入的網址來自此安裝的裝置設定，不含發布方帳戶或歷史測試 URL。

其他電腦不需安裝 Codex／Claude、不需供應商登入；只需要供應端在線、HTTPS endpoint 與有效 key。供應端重啟／更新／同帳戶重部署沿用原 URL 與 key；重新安裝到全新資料目錄則視為另一裝置。

## 第三方 agent 應驗收

1. 將 key 放入該專案的服務端 secret，環境變數名為 `LLM_BRIDGE_KEY`。base_url 使用標準訊息給的 `/api/v1`；不要再重複加 `/v1`。
2. GET `<base_url>/models` 帶 Bearer key，確認指定模型存在。key 來源 scope 也必須允許該 provider；不代表任意模型都可用。
3. POST `<base_url>/chat/completions`，只送 `model`、`messages`、`stream:false`。設合理 User-Agent、100 秒 timeout、停用自動重試。
4. 核對真實文字與數值型 `usage.cost`。其值是 USD 牌價估值，非 OpenRouter 實際帳單，無需 OpenRouter key。
5. 檢查client/SDK是否偷偷附加temperature、token上限、provider路由或stream。非等價參數回400，不能把錯誤吞掉。0.6.3支援最多256個工具定義及tool_choice／工具歷史，需符合原函式schema；不會代執行本機工具。provider.data_collection=deny/allow可作路由相容欄位。
6. 模擬供應端關閉／無效 key，確認消費端能顯示 503／401，不會無限重試或默默改用其他付費供應商。

## 模型查詢與 Jev 使用端

先 GET origin + /bridge/v1/model-capabilities；依 availability、證據時間及 key scope 選模型，不把模型選單當成訂閱權限。需要即時重讀時 POST /bridge/v1/models/refresh，body 為空 object；查詢不執行推論。POST /bridge/v1/models/probe 會消耗用量，只接受 model 與 protocol（chat／decisions）。

原本的 Jev 使用端只換完整 URL 至 origin + /api/alpha/decisions、key、model，保留 state／questions 及 answers 解析。可建議裝置已驗證可用的 Luna／Haiku，不隱藏換模型。三種題型、成本、收據及限制見 [Jev 相容指南](JEV-COMPATIBILITY.md)。機率為一般 LLM 估計，原門檻需重測；每題實際呼叫成本加總，未知用量不當成免費。

新路徑需 Worker、Relay、Bridge 都更新；僅本機測試不等於外部端點驗收。

## 適用範圍

| 消費端 | 接入方式／阻力 |
|---|---|
| Web 服務後端、Cloud IDE 上的程式 | 可改 base URL、key 與少數預設參數；用 OpenAI Chat Completions 的非串流 HTTP adapter |
| AI IDE 裡編寫／執行的應用程式 | 可接入；由 agent 修改該應用程式的 provider，不代表 IDE 本身的 agent 引擎也相容 |
| IDE 自身的 agent provider | Chat Completions工具可按能力串接；若必須用串流、Responses或原生Anthropic協定，目前不相容，不能保證只換URL/key即可工作 |
| 跨來源瀏覽器 JavaScript | 需經自己的 Web 後端代理；Bridge 無公開 CORS，key 不能進前端 bundle |

單次標準 POST 約 90 秒。不要讓 SDK 自動重送逾時 request。供應端原始 I/O 不落地、只存中繼資料；消費端 IDE／平台是否保存 prompt，需由該端自己管理。


0.6.3：[AI EA Cloud 整合、成本、端點與供應裝置交接](AI-EA-CLOUD-BEST-PRACTICE.md)。獨立Cloud/client路徑已驗真實訂閱與原帳本，原生安裝UI仍單獨驗收；Mac等待實機驗證。

0.6 AI EA 相容補充：provider.data_collection=deny/allow 可原樣傳入，Bridge 將其作路由相容欄位，不影響接單；Cloud 不提供訂閱政策核准開關。其他尚無對應能力的 provider 路由參數仍會明確回 unsupported_parameter。


標準容量為每裝置 64 筆同時推論，Claude／Codex 與 Chat／Decisions 共用。請以普通同步 API 並行 POST（async/await、Promise.all 或連線池），每筆直接取得結果；串接不需工單或輪詢。新 key 預設 600 RPM，既有 key 頻率另行核對。超過 64 尚待驗證，詳見 [併發規格](CONCURRENCY.md)。
