# 現行 Windows 安全邊界與更新

適用已發布 Windows 0.8.1 安全修補、0.8.2 listener 與 0.9.0 Jev／模型查詢。0.8.1 包含核心 0.6.7；0.8.2 核心識別為整合後 0.8.1-mac.1；0.9.0 核心同號，不另發布 Mac。發布／安裝驗收狀態見 [ACCEPTANCE](ACCEPTANCE.md)。這不是完整 OpenRouter 等價或整台電腦零痕跡保證。

## 流量與權限

第三方以 HTTPS、長效 client KEY 呼叫安裝者自己的 Worker。Worker／Cloudflare 終結 TLS，因此會接觸原文與 client KEY；DEVICE_KEY 可冒充裝置，必須與一般 client KEY 分開保護。本機只監聽 loopback，Relay 主動向外 poll，不能轉送管理端點。client KEY 不取得本機管理 token，也不能讀其他 KEY 的工作結果。

Relay 一律拒絕 redirect，包括同來源，避免憑證被帶到其他主機或 HTTP；poll 回應最多 6.1 MB（涵蓋 3 MB request 的字串跳脫），ack 最多 1 KB。超限或格式錯誤只顯示固定連線狀態，不記錄 payload／headers／例外原文。

Windows 0.8.2 原生入口另將 API／管理 listener 設為 `SO_EXCLUSIVEADDRUSE`，關閉 `SO_REUSEADDR`，避免另一個本機程序重綁同一 loopback 位址／埠而接收不確定的流量。這需要攻擊者已能執行本機程序，並非外網未授權入侵的證據。來源／Mac 入口不套用 Windows socket 選項；Windows 修補不代表其他安裝格式已更新。既有埠遭占用時新服務必須失敗，不搶占既有服務；獨占綁定不防同一 OS 使用者已被接管或服務啟動前的埠搶占。依據 [Microsoft Winsock 說明](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse)。

## 內容不落地與 CLI

Bridge 只持久保存 allowlist metadata、牌價、設定與 OS 保護憑證。請求／結果經 RAM、stdin/stdout pipe 與 loopback；不建立 prompt／schema 暫存檔，不把 caller 內容放在 argv。Claude 的 caller system／developer 指令與外部 response schema 以 stdin 包裝後處理，使用固定服務 system prompt；不是原生 API system role 或 CLI `--json-schema` 的完全等價映射。自有 Decisions 僅將 repo 產生的固定結構／陣列長度交給原生 `--json-schema`，argv 沒有 state／instructions／criteria 名稱或外部 schema。Structured output 仍由 Bridge 驗證，不符合回 502，已發生的 token／成本仍留回執。

Codex 使用 ephemeral thread、拒絕非允許工具事件；Claude 使用 restricted、空 tools／MCP、停 session persistence。共用 provider environment 採 OS／訂閱目錄／proxy 必要項 allowlist，不傳一般雲端秘密。Windows Job Object 只管理自有程序，不是阻擋所有本機檔案讀取的 OS sandbox；CLI 版本變更仍需負面測試。不操作其他正在使用的 CLI session 或全域登入。

Bridge 不聲稱控制供應商／Cloudflare 內部保留、Windows pagefile／dump／EDR、瀏覽器／clipboard 歷史。KEY label、自訂模型名稱也屬管理資料，不應放入敏感訊息。Windows DPAPI 不保護同一 OS 使用者已被接管的情況。

## Schema 運算預算

Windows validator Job Object 另限制單程序 commit memory 256 MiB；工具提案一樣受時間／並行／輸入預算限制。Claude 若只回一個完整 JSON code fence，可去除外框後再嚴格驗證；不擷取混雜說明、不修補 JSON、不自動重送付費推論。

response_format 與工具參數 schema 先檢查 aggregate ≤256 KiB、≤8192 nodes、深度≤24，不接受 `$ref`／`$dynamicRef`（含本地引用）。超限／引用回 400 unsupported_parameter；無效定義回 400 invalid_request。Schema 檢查與輸出驗證放在獨立自有程序，單次最多 3 秒、最多同時 4 個；過載回 429，輸出驗證失敗或超時回 502。程序 stdin 承載內容、stdout 只有固定結果，無原文檔或 traceback。

Worker 範本把正在讀 body 的工作一併計入總上限 9，body 讀取 deadline 15 秒。**Windows 更新不會自動部署 Worker**；既有 BYO 安裝者須另行授權更新原 Worker，沿用帳戶／名稱／DEVICE_KEY／URL／client KEY。來源測試通過不代表雲端部署已修補。

## 依賴與供應鏈

Windows builder 最低 Python 3.14.9／OpenSSL 3.5.9／certifi 2026.10.19；實際值與 CA SHA256 寫入 self-test。此 CA 修補對應 [certifi 維護者公告](https://github.com/certifi/python-certifi/security/advisories/GHSA-6q48-6c7w-9gw2)。版本基線是當期最低要求，仍需持續 CVE 查詢。

Windows 全依賴及 announce signer 子集使用 published artifact SHA256 鎖檔，安裝時 `--require-hashes`；更新鎖檔工具 `packaging/windows/refresh_lock.py` 不執行下載套件程式。Wrangler 4.152.0 與 transitive dependencies 固定於 `cloudflare/package-lock.json`；用 `npm ci --ignore-scripts --prefix cloudflare`，或由安裝者更新經驗證的全域 CLI。Node 安全基線：22.23.4+、24.22.1+、26.12.1+；helper 不默默修改全球 Node／Wrangler。

`tools/audit_dependencies.py` 只送套件名稱／版本到 OSV，查鎖定 Python、Wrangler 子樹及 Velopack；失聯、不完整結果或命中都不放行。Windows build/publish 與每日 security workflow 執行，不能把 OSV 無命中當作 native CLI、Windows、WebView2、workerd 或未知漏洞的完整 SBOM 驗證。Windows／共用 CI 第三方 actions 固定 commit SHA；Mac workflow 不在本次變更範圍。

既有安裝以原 Ed25519 公鑰驗更新 policy、target／sequence／有效期與套件 hash；不換 signer。初次未簽 Authenticode 的安裝包仍需可信下載來源，更新 hash 不取代初次信任。環境 signer、repository／environment 權限與帳戶 MFA／review protection 由擁有者管理，本次不擅改組織授權。

## 回報與修補驗收

不要把憑證、正式 I/O 或未修漏洞的詳細 exploit 發到公開 issue。先私下整理受影響版本、觸發條件與合成重現證據。修補需有 source／native package／真實呼叫／更新前後裝置保留證據，再宣布。單一 canary 未成功不能宣稱沒有任何檔案存取風險。

## 0.9 Decisions／模型查詢延伸

新增 Decisions 仍使用同一 KEY、queue、RPM、deadline 與無工具 provider。state／題目／答案只在 RAM／stdin，生成 schema 先整體檢查，輸出用同一受限 validator；題目不納入 log。每次呼叫先保存已核對用量及 cache／reasoning metadata，再驗語意／下一題；模型缺失／不符或用量未知不得顯示成完整零成本。新 protocol／呼叫計數僅 additive metadata，不回填原有列。

0.9 也在 Windows 共用啟動入口安裝同一獨占 listener adapter，涵蓋新版 source／ZIP；原生入口保留保護。Windows background 若埠占用則安靜回 exit 2，不跳出 Tk 對話框或搶占埠；Mac 分支不變。直接嵌入 Python 類別的開發者仍須自行選擇適當 server adapter，不將這些 entrypoint 保護宣稱成 stdlib 全域保證。

模型發現僅以 stat metadata 識別登入世代，不讀取／輸出 auth.json；唯讀 Codex model/list 不建立推論 thread。refresh 最短 5 秒合併、一般快取 30 秒，避免重複持 KEY 探查啟動 CLI。這不是防已接管 OS 的隔離，也不代表 picker 目錄證明訂閱權限。新路徑只交付 Worker 範本，未獲部署授權時不得聲稱外部新路徑已修補／可用。

## 0.9.7-mac.1 驗證預算（D-34／D-35）

修訂前述歷史預算：外部 schema 保留四個一次性子程序，每次至多 3 秒，名額等待至多 30 秒，兩者均受 request 剩餘期限／取消約束。昂貴驗證前保留受理容量。Decisions 自有結構改固定欄位／長度／型別／有限值／0–1 驗證，JSON 至多 1 MB／深度 4；不提供外部 schema 程序內快速路徑。Windows 256 MiB Job Object 保留；Mac 只有既有輸入／複雜度／時間／並行預算，不宣稱相同 OS RSS hard limit。

移除 queued spec 後釋放引用，worker 空閒清掉上一筆 spec；終態錯誤保存新的固定診斷，不保留 caller exception traceback。CLI stdin 也有取消／期限，避免不讀 pipe 的子程序永久卡住。分段時間僅接受 SCHEMA 的固定數字，未知 ready 為 null。公開取消限制與效能門檻見 [計畫](PERFORMANCE-PLAN.md)。

推論前僅合併同 provider／auth generation、時間重疊的 auth status；完成即移除，沒有 TTL／憑證快取。等候者維持自己的期限／取消，查詢子程序由 Bridge 獨立擁有並清理。Claude 自有 Decisions 的 20 ms 啟動間距等待也受同一預算約束，等待後再核對 generation；沒有常駐推論 CLI。

## #39 實驗邊界

單次 Codex transport 的 stdout 以 4 MB 單行、8 MB 待處理 bytes 與 4096 筆限制；stderr 丟棄。預熱不建立 thread／turn，不接收 Key、model、system 或 request；領用後不可歸還重用。generation 失效、取消、pause、TTL 及 stop 清理自有程序與空 cwd；清理失敗保留 counted slot、停止補池。實驗工具不加入正式服務，無新的 KEY／憑證檔；Mac 尚無全裝置 RSS／CPU hard limit，相關預算未放行。[完整契約](WARM-CLI-PLAN.md)。

Windows 原生文字複製使用同一呼叫執行緒建立的 message-only window 作為 OpenClipboard／EmptyClipboard owner，不借用其他 app 的前景視窗。成功後 Windows 接管記憶體，失敗時本程序釋放；兩種情況均清理隱藏視窗。來源與外部導覽檢查保留。

## Mac 明確啟用的單次常駐（0.9.9）

Codex 常駐只做 initialize／initialized；沒有 caller key、模型、prompt、thread 或 turn。一個 lease 只執行一題，無工具與空 cwd 及原 event/line/buffer 上限保持，關閉程序與 pipe 後才刪目錄並釋放 slot。auth／binary／config stat generation 改變、TTL、異常 idle 工作事件均淘汰；開始後失敗不重送。active、idle、refill、closing 共用兩 provider 的推論 root limit，Claude cold 也占相同名額；補池讓位於受理驗證／排隊／執行滿載與 lease 等候者。唯讀 auth/model 與外部 schema 的既有控制預算分開，這不是 Mac 程序樹 RSS／CPU hard limit。清理失敗保留 quarantined 名額並停止池，不虛報可用容量；request monitor 仍持續處理取消與期限。

常駐預設 0，只有明確 owner 選擇的 Mac operator 試驗才開啟；管理認證 API 要求 paused＋idle，三容量整數驗證後同一 transaction 套用，DB 失敗不留下半套設定。原文／事件／stderr 只在管線與 RAM，warm/cold 次數為 numeric metadata。完整隔離／尖峰／資源門檻仍見 [計畫](WARM-CLI-PLAN.md)。
