# AI EA Cloud：Bridge 優先整合

狀態：0.6.0 開發與離線驗證中。以下是可重現配置與驗收步驟；正式 Cloud／地端安裝版整鏈尚未驗收，不是已成功上線案例。

## 架構

地端 AI 特助上線 → 既有 AI EA Cloud（JWT、會員、預扣）→ Bridge 優先／OpenRouter 備援 → 單次結算。管理端可切優先順序，地端不改 URL、不提供 Bridge key、不調 MCP／CLI 授權。Bridge usage.cost 直接是 Cloud 成本，例如 1.54 記入既有 cost_usd 並扣會員額度；request provider 記是哪個 Bridge 或 OpenRouter。Cloud 對地端移除金額，剩餘百分比沿用既有 SQL。

## 安裝與端點

1. 按 BYO-QUICKSTART.md 在供應者自有 Cloudflare 帳戶安裝，保留其原 profile／Worker。以原資料目錄更新 0.6.0 並部署新版 Worker，核對本機版本與公開 HTTPS。
2. 從設定讀取公開 origin；不得使用歷史驗收網址當預設。建立獨立服務 key，明文僅一次交給 Cloud secret。一般串接 base URL 為 `<origin>/api/v1`，Cloud registry 的 base_url 則只填 `<origin>`，防止重複 `/api/v1`。
3. Cloud 設定 `AIEA_BRIDGES=[{"id":"bridge:office","base_url":"https://YOUR-WORKER.workers.dev","key_env":"AIEA_BRIDGE_KEY_OFFICE","models":{"REQUESTED-MODEL-ID":"ACTUAL-BRIDGE-MODEL-ID"}}]`，key 存 `AIEA_BRIDGE_KEY_OFFICE`。映射由管理者明確指定，回應保留實際模型。
4. `AIEA_LLM_PRIORITY=auto` 採管理頁，或環境覆寫 bridge_first/openrouter_first。管理頁停用 Bridge 可立即回 OpenRouter。更新正式 secrets 不用重新部署；只改本機 .env 不會改線上。
5. Cloud 不審核 Bridge 訂閱政策，不設核准開關。provider 原樣轉送；Bridge 接受 data_collection=deny/allow 作路由相容欄位，不影響接單，也不宣稱已驗證訂閱政策。條款與 MCP/CLI 授權不變。

本機推論埠從 profile 的 port 讀取（原預設 8920），管理台使用 launcher 提供的 loopback URL，不能把管理埠曝露至公網。公網為 HTTPS 443；Cloud 不需要供應機器 IP。改本機埠需要重啟 Bridge；切 Cloud 優先順序不需要。更換供應機器可註冊另一個 endpoint／key，先驗 ready，再排空舊機並更新 registry；沒有跨 Windows 使用者自動解密承諾。

## 能力與保活

新增 POST `/bridge/v1/preflight`，同一 Bearer key 與 chat body，驗參數、模型 scope、接單與容量，不推論、不記費。subscription_verified=false 表示供應商登入仍在執行時驗；不是把 relay 在線當成真實推論成功。

工具輸入以保留角色的結構化對話封裝，模型產生符合 envelope schema 的提案；結果轉 OpenRouter tool_calls，校驗函式名與 arguments。這是工具提案 adapter，不是開放本機 shell/MCP。工具結果要有對應 tool_call_id；不支持的 schema 引用／多模態組合回 unsupported_parameter，由 Cloud 備援。串流、Jev decisions、embeddings 不冒充等價能力。

Cloud deadline 下傳供應端，包含排隊與執行；request ID 隔離於 API key 並保留 metadata 去重。結果只在 RAM 留 10 分鐘，重啟後拒絕重播。已確認本機子程序終止的逾時可由 Cloud fallback；未知執行狀態不自動再次推論。Relay 斷線採退避＋抖動，心跳過期視為離線。供應機器睡眠／關機時由 OpenRouter 承接，不宣稱保活能喚醒機器。

## 驗收與交付

先跑 Bridge pytest／Worker tests／字詞檢查，再 AI EA Cloud Deno／SQL／DOM 與 AI EA 全套離線閘門。真實路徑必須驗文字、JSON、工具提案與結果回傳、兩種優先順序、停機 fallback、key 失效不登出、cost_usd/剩餘%一致、重送不重扣。用正式 project 的專用 e2e-test 帳號驗真 reserve/settle；清理只限本輪 ID。

最後以既有安裝版 AI 特助上線驗收完整思考鏈，核對資料、登入、AI 開關、預算、保險絲、送出閘門不變。不發真 LINE 測試訊息。來源、部署、套件、實際安裝更新分別列證據。測試 key 撤銷後仍保留一把 Cloud 正式服務 key，不能留下無法呼叫的安裝。
