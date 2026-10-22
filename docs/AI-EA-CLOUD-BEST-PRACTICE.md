# AI EA Cloud：Bridge 優先整合

狀態：Windows Bridge 0.6.3 已發布；正式 Cloud、原版 client 與本地訂閱的獨立合成帳號路徑已通過真實核帳。原帳號的原生 UI 整鏈尚未驗收，不能將 client API 測試當成全部功能上線。macOS 等待實機驗證；本 Windows 工作不發布 macOS release。

## 架構

地端 AI 特助上線 → 既有 AI EA Cloud（JWT、會員、預扣）→ Bridge 優先／OpenRouter 備援 → 單次結算。管理端可切優先順序，地端不改 URL、不提供 Bridge key、不調 MCP／CLI 授權。Bridge usage.cost 直接是 Cloud 成本，例如 1.54 記入既有 cost_usd 並扣會員額度；request provider 記是哪個 Bridge 或 OpenRouter。Cloud 對地端移除金額，剩餘百分比沿用既有 SQL。

## 安裝與端點

1. 按 BYO-QUICKSTART.md 在供應者自有 Cloudflare 帳戶安裝，保留其原 profile／Worker。Windows 以原資料目錄更新目前 Windows release（0.6.3 以上） 並部署對應 Worker，核對本機版本與公開 HTTPS；macOS 另依原始碼安裝流程實機驗證，不能套用 Windows EXE／DPAPI。
2. 從設定讀取公開 origin；不得使用歷史驗收網址當預設。建立獨立服務 key，明文僅一次交給 Cloud secret。一般串接 base URL 為 `<origin>/api/v1`，Cloud registry 的 base_url 則只填 `<origin>`，防止重複 `/api/v1`。
3. Cloud 設定 `AIEA_BRIDGES=[{"id":"bridge:office","base_url":"https://YOUR-WORKER.workers.dev","key_env":"AIEA_BRIDGE_KEY_OFFICE","models":{"REQUESTED-MODEL-ID":"ACTUAL-BRIDGE-MODEL-ID"}}]`，key 存 `AIEA_BRIDGE_KEY_OFFICE`。映射由管理者明確指定，回應保留實際模型。
4. `AIEA_LLM_PRIORITY=auto` 採管理頁，或環境覆寫 bridge_first/openrouter_first。管理頁停用 Bridge 可立即回 OpenRouter。更新正式 secrets 不用重新部署；只改本機 .env 不會改線上。
5. Cloud 不審核 Bridge 訂閱政策，不設核准開關。provider 原樣轉送；Bridge 接受 data_collection=deny/allow 作路由相容欄位，不影響接單，也不宣稱已驗證訂閱政策。條款與 MCP/CLI 授權不變。

本機推論埠從 profile 的 port 讀取（原預設 8920），管理台使用 launcher 提供的 loopback URL，不能把管理埠曝露至公網。公網為 HTTPS 443；Cloud 不需要供應機器 IP。改本機埠需要重啟 Bridge；切 Cloud 優先順序不需要。更換供應機器可註冊另一個 endpoint／key，先驗 ready，再排空舊機並更新 registry；沒有跨 Windows 使用者自動解密承諾。

## 能力與保活

新增 POST `/bridge/v1/preflight`，同一 Bearer key 與 chat body，驗參數、模型 scope、接單與容量，不推論、不記費。subscription_verified=false 表示供應商登入仍在執行時驗；不是把 relay 在線當成真實推論成功。

工具輸入以保留角色的結構化對話封裝，最多256個定義；已驗131工具的主串、提案及結果續答。模型產生符合精簡 envelope schema 的提案，轉 OpenRouter tool_calls 後再校驗原函式名與 arguments。這是工具提案 adapter，不是開放本機 shell/MCP。工具結果要有對應 tool_call_id；不支持的 schema 引用／多模態組合明確回錯，未推論時可由 Cloud 備援。

原版 AI EA 的 typed decisions 在 Cloud 轉為 chat structured output；實際模型由 registry 指定。noul／choice／score 是附證據的類別，不是 Jev 校準機率。Cloud 依既有 kind=gate 還原原版固定次要題清單；次要題未知只留無訊號，必要題未知仍錯誤。這段應用協定不放進 Bridge。embeddings／搜尋等未具備能力仍需 OpenRouter；不宣稱整套 OpenRouter 或所有 AI EA 功能均可純本地運行。

Cloud deadline 下傳供應端，包含排隊與執行；request ID 隔離於 API key 並保留 metadata 去重。131工具preflight上限8秒，Cloud整筆50秒、優先Bridge單次38秒。結果只在RAM留10分鐘，重啟後拒絕重播。已知成本在輸出驗證前保留；Cloud以唯讀receipt復原遺失回應或結算已知錯誤成本。完全失聯且無usage時仍屬未知，不能承諾所有中斷都能立即取得精確成本。原版client未帶UUID，不能宣稱已涵蓋其跨HTTP重試去重。

已確認本機子程序終止的逾時可由Cloud fallback；未知執行狀態不自動再次推論。Relay斷線採退避＋抖動，心跳過期視為離線。睡眠／關機前尚未派送的新請求可轉OpenRouter，已派送但未知的工作不能盲目重做。不宣稱保活能喚醒機器。

## 驗收與交付

先跑 Bridge pytest／Worker tests／字詞檢查，再 AI EA Cloud Deno／SQL／DOM 與 AI EA 全套離線閘門。真實路徑必須驗文字、JSON、工具提案與結果回傳、兩種優先順序、停機 fallback、key 失效不登出、cost_usd/剩餘%一致、重送不重扣。用正式 project 的專用 e2e-test 帳號驗真 reserve/settle；清理只限本輪 ID。

最後以既有安裝版 AI 特助上線驗收完整思考鏈，核對資料、登入、AI 開關、預算、保險絲、送出閘門不變。不發真 LINE 測試訊息。來源、部署、套件、實際安裝更新分別列證據。測試 key 撤銷後仍保留一把 Cloud 正式服務 key，不能留下無法呼叫的安裝。

原版自己的有效OpenRouter key仍優先，byok座位也沒有Cloud AI額度；只把Bridge key存到Cloud不會自動切換這個使用者。原帳號方案、預算與來源設定須有明確授權，不能為通過驗收而繞過。先以獨立合成帳號驗供應端，原帳號UI另列閘門。

## 下一階段：改用另一台 Mac 作常駐供應端

此段為交接與驗收計畫，不表示Mac已可正式使用；不在目前Windows工作啟動Mac部署或發布Mac安裝包。AI EA仍呼叫同一Cloud URL，Cloud改供應端不需修改AI EA／MCP／CLI授權。

1. 新Mac從repo的[安裝流程](CROSS-PLATFORM-INSTALL.md)建立自己的裝置profile與BYO Worker，先核對安裝者自己的Cloudflare帳戶。新裝置有自己的device_id、HTTPS URL與長效client key；不要搬Windows DPAPI、覆寫原Windows profile或將原網址當預設。Codex訂閱登入與裝置key獨立，同一profile切訂閱不應改URL/key，須在Mac實測。
2. 由Mac擁有者完成Codex訂閱登入，檢查Keychain可用。先從異地GET models、preflight、真實POST驗外部HTTPS，不以本機localhost或relay在線當成功。模型依實際可用清單與OpenRouter對應牌價設定，不沿用其他裝置的模型假設。
3. 新增獨立Cloud secret（例如AIEA_BRIDGE_KEY_MAC_PRIMARY）；key僅在可信服務端secret安全輸入，不貼聊天／repo／log。registry可用新裝置別名bridge:mac-primary，base_url只填origin。候選階段只加測試別名，例如probe/mac-main→Mac實際主模型、probe/mac-judge→Mac實際小模型，不搶走舊Windows的正式模型映射。Cloud先按request model篩選候選，因此獨立測試可直接用這些別名，同一Cloud URL／原版client即可，其他正式呼叫仍走原供應端。保留舊Windows registry與secret，Mac尚未驗收前不撤銷原key。
4. 正式切換前用獨立合成帳號與候選別名驗文字、JSON、多輪、完整131工具／結果、typed判斷與Gate次要題／必要題、錯誤不登出、已知錯誤成本與receipt。Gate的judge_model可在驗收程式設定為測試別名，不修改AI EA產品程式。逐筆讀回實際provider、實際model、token、cost_usd、quota delta及預扣歸零；不能只看200或答案。只存metadata，清理本輪帳號與暫用key。
5. 驗同一profile重啟Bridge、更新及同帳戶重部署後URL/key不變；測斷網重連、睡眠／喚醒、CLI登入失效及Keychain鎖定。LaunchAgent是登入後啟動，不是未登入開機即服務；常駐機需供電與合適睡眠設定，須由Mac擁有者決定。未知已派送工作不得在重連時重播。
6. 驗收後才將Cloud正式registry切到Mac，保留OpenRouter fallback。先排空Windows已派送工作，再核對正式流量的provider和成本帳；失敗時恢復舊registry／secret，或停用Bridge切回OpenRouter。不改會員原帳本，也不自動輪替原Windows key。雙方確認穩定後才決定舊機退役。
