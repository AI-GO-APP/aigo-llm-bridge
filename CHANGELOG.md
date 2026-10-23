# Changelog

## Windows installer 0.8.1

- Update the Windows runtime to Python 3.14.9, OpenSSL 3.5.9 and certifi 2026.10.19; enforce the security baseline before packaging.
- Refuse Relay redirects and bound cloud response reads; keep device URL, client keys and metadata unchanged.
- Send caller Claude instructions and schemas only over stdin, and validate schemas in bounded disposable processes with no payload logs.
- Reserve Worker queue slots before body I/O; ship the corrected BYO template without deploying any installer's Worker.
- Pin audited Wrangler/Node prerequisites, hash-lock Python artifacts, pin Windows/shared CI actions and add daily/pre-release dependency gates. No Mac release or Cloud deployment.

## Windows installer 0.8.0

- Add resumable first-install onboarding for subscription CLI authorization, BYO Cloudflare login, explicit account selection, one-click deployment and AI IDE collaboration.
- Limit the reversible AC policy to automatic sleep, hibernate and unattended sleep; preserve screen locking, display, physical buttons and DC settings. Use ordinary permissions first, with an explicit power-only UAC fallback.
- Require a real HTTPS models/chat check with numeric usage.cost and long-lived key handoff before completing setup; retain device data and completion across updates.
- Document CI/CD and Release operations, evidence gates, recovery and installer onboarding in the bundled product handbook.

## Windows installer 0.7.3

- Adopt the contract/billing console visual system across all six Bridge pages, light/dark themes and Windows settings.
- Add the product documentation index, requirements, architecture, full SQLite dictionary, API compatibility, design system, decisions and acceptance matrix; bundle them with Windows and check drift in CI.
- Preserve device URL, key scope, metadata and provider logins; no Cloud deployment or Mac release.

格式參考 [Keep a Changelog](https://keepachangelog.com/),版本號遵循 [SemVer](https://semver.org/)。
0.x 期間 API 可能變動,每次變動都會寫在這裡。

## [Unreleased]

## [0.9.0] - 2026-10-23

- Add caller-scoped model discovery, timestamped capability evidence and explicit synthetic probes without treating picker lists as subscription entitlement.
- Add Jev-compatible Decisions for noul, choice and score; isolate each question, validate through bounded schema helpers and preserve actual-model usage and incomplete billing receipts.
- Include Decisions/discovery examples in Windows setup, BYO/AI IDE handoff and the shared console; preserve the device endpoint, long-lived keys, metadata and Windows 0.8.1/0.8.2 security controls.
- Ship Worker route/template updates without deploying existing Cloud endpoints or releasing Mac packages. New external routes require a separately authorized Worker update.

## [0.8.1-mac.1] - 2026-10-23

同步 Windows 0.7.3 六頁設計、0.8.0 首次設定及 0.8.1 共用安全修補，新增 Mac WKWebView、原生剪貼簿／CSV、AC 自動睡眠同意與還原、KEY／HTTPS 交付及安全來源更新。

### 升級影響
- Mac：需更新來源安裝並重啟，保留原 profile、URL、有效 KEY、模型與推論容量；不自動改電源或登入。
- Windows：只共用設定流程的可覆寫平台方法，不更新其已安裝服務或發布渠道。
- Cloudflare／呼叫端：協定不變，不因這次本機更新重建 Worker 或重發 KEY。
- 發布：Mac source 候選，不建立 tag／Release／DMG；驗收範圍見 docs/qa/2026-10-23-macos-parity.md。

## [0.6.7] - 2026-10-23

Shared security fixes for the Windows 0.8.1 release: redirect refusal, bounded schema validation, minimal provider environment, stdin-only caller data for Claude, and an atomic BYO queue template. This core source version does not publish or upgrade macOS or any Cloudflare deployment.

## [0.6.6-mac.2] - 2026-10-23

Mac source 實機修復候選，不建立 tag／Release、不發布安裝包。設定檔可明確選擇 1–4 個隔離推論子程序，預設維持 1；Mac CLI 先 pause／wait-idle 再重啟。此 Mac 改為 4，消除實測短請求排隊耗盡 Cloud 期限的瓶頸。原 KEY、模型 scope、endpoint、去重與 metadata-only LOG 保留，Windows 正式服務／Worker／裝置資料不變。

## [0.6.6-mac.1] - 2026-10-22

Mac source 驗收候選，未發布任何 macOS／Windows release 或安裝包。補 owner-only SQLite、穩定 LaunchAgent 更新與 rollback、一次性本機 key 交付、cache/reasoning 用量 metadata，以及首次配對後程式重新部署。本輪實機與 Cloud 驗收見 Mac QA；既有 Windows 服務與裝置設定保持原狀。

### 升級影響
- Mac：依 source 安裝流程明確更新；既有設定檔、endpoint 與有效 key 保留。
- Windows：不更新或重啟正在執行的服務，不改 Worker、裝置資料或 key。
- CI：以已核對的 Git 作者別名保留原始歷史並繼續檢查標準名稱；新增身分對應及發布保護回歸。
- 發布：`-mac.*` 候選版本合併不自動建立 tag／Release；本輪不發布任何新安裝包。


## [0.6.5] - 2026-10-22

- CI 將合法協作者尾欄 email 與既有作者 email 採相同身分規則，修正 GitHub 自動合併的誤判；作者名稱、產品檔案、一般訊息與非尾欄仍完整檢查。
- 新增六項規則邊界回歸，保留已發布版本與歷史，不改寫 tag。推論行為仍與 0.6.3 相同。
- 包含 0.6.4 的供應裝置交接指南，只發布 Windows 安裝包，不更新正在執行的安裝或發布 Mac。

## [0.6.4] - 2026-10-22

- 更新已驗證的 Cloud／原版 client 相容邊界、131 工具與成本／receipt 指南；原生 UI 仍待獨立驗收。
- 加入下一階段 Mac BYO 常駐供應裝置的安裝、測試、切換與回退交接；本次不發布 Mac。
- 依既有 CI 規則，隨附文件更新亦提升套件版本；推論行為與 0.6.3 相同，不自動更新或重啟現有安裝。

## [0.6.3] - 2026-10-22

- 支援最多 256 個工具定義，涵蓋 AI EA 的完整 131 工具集；精簡模型輸出 schema，回傳後仍逐工具驗證 JSON arguments。
- 結構化輸出或工具參數驗證失敗，仍保存供應商已回報的 token／成本中繼資料，供 Cloud 原帳本結算。
- Windows 原安裝更新／重啟與 URL／KEY 保留通過；95 項 Python 回歸通過。
- AI EA 原生安裝 UI 未驗收，不把來源或 API 測試代替；不發布 macOS。

## [0.6.2] - 2026-10-22

- Windows：preflight、request ID 去重、執行期限及文字工具提案／工具結果歷史；工具仍由呼叫端執行。
- 新增同 KEY 的唯讀 receipt，復原 RAM 結果與已知 token／cost，不保存原文或重複推論。
- BYO 升級不重寫相同 transport secret，避免啟用舊 Worker；裝置 URL 與 client KEY 保留。
- OpenRouter 非等價參數仍明確拒絕，串流與完整 IDE agent 相容性不列為已支援。
- Windows 真實更新、重啟與訂閱成本核對通過；AI EA 原生安裝 UI 仍獨立待驗，macOS 不發布。
- 舊 Hosted／worker／Python client 僅同步版本常數，無行為變更或部署。

## [0.5.0] - 2026-10-22

Windows 新版改採裝置擁有的 BYO Cloudflare 公開 HTTPS 入口，提供本機管理台、長效 API key 及可交給遠端 IDE 的串接訊息。macOS BYO 實機流程仍待驗證，本版只發布 Windows 原生安裝包。

### 升級影響
- Windows 0.3.x BYO 安裝：以同 InstallRoot 更新並沿用 data_dir，保留 UUID、URL、key hash 與 metadata；先暫停及排空工作，不重開電腦。
- 舊的 desktop 個人端點：與 BYO 設定檔不同，沒有自動搬移其明文 key 或改寫登入。依 BYO 指引建立自己的 Worker。
- macOS：不觸發發布、不改 macOS 安裝及封裝程式碼；本輪未做實機驗收。
- Hosted／舊 worker／客戶端：無行為變更，只同步根版本號；不需部署或修改平台表。
- 不需要 OpenRouter API key：成本來自公開模型牌價，usage.cost 為 USD 估值。

### Added
- Windows Web Console、長效 key 的建立／輪替／撤銷、僅 allowlist metadata 的 LOG 管理。
- 固定 Worker、裝置配對與帳戶綁定；CLI 訂閱登入切換不影響 URL/key。
- OpenRouter 部分相容 POST/GET、非等價參數明確 400，以及實際 token/cache 牌價換算。
- repo 隔離安裝器、doctor、自有 Cloudflare agent 指引、一次性 key 串接訊息。
- Windows CI 實際建置、原生 EXE 隔離 smoke、文件連結及隱私檢查，發布 manifest 含來源 commit 與 SHA256。

### Fixed
- 新設定檔與新建 UI key 預設 Codex；一般設定儲存保留既有明確的預設模型，不意外切到 Claude。
- Windows 中文 CLI 輸出統一 UTF-8；Python 呼叫端需使用有效 CA bundle，保留 TLS 驗證。


## [0.4.0] - 2026-10-22

新增 Mac／Windows 個人本機端點，沿用本人 Claude Code 與 Codex 訂閱登入，並各自安裝與發布。

### 升級影響
- Bridge：不需要重新部署；Hosted 路由與 worker 協定不變。
- 表與環境變數：不需要。
- worker：不需要更新；新個人端點為選用元件。
- 客戶端：不需要重新複製。個人端點只供本機本人使用。

### Added
- 個人端點、CLI 登記、隨機 Bridge 金鑰與非串流文字對話。
- Mac LaunchAgent 與 Windows 使用者排程安裝、更新、移除。
- 共用核心／獨立平台／獨立封裝分層，兩平台各有 CI 與可單獨發布的 CD。
- 安裝包 manifest 記錄來源 commit、平台、版本與 SHA256。


### Fixed
- 直接用瀏覽器開啟個人端點改顯示連線設定頁，提供金鑰取得與測試方式，避免誤認為服務故障；API 驗證仍保留。

## [0.3.0] - 2026-09-28

**破壞性:移除 0.2.0 加入的 Agent Skill 包裝與自動同步。** 這個 repo 是可部署的產品與範例,不是 skill;
自動強制同步對部署用的 clone 有風險。裝過 0.2.0 SessionStart hook 的人,請把設定裡指向
`tools/check_update.py` 的那一項拿掉,用 `npx skills add` 裝過的副本可以直接刪掉。
取而代之的是完整的使用說明:依角色的閱讀路線、取得與更新、機敏資訊、本機開發、工具總覽。

### 升級影響
- Bridge:不需要重新部署(程式行為沒有變,只有版本號)
- 表、環境變數:不需要
- worker、客戶端:不需要更新;從這一版起可從 Release 直接下載
- 裝過 0.2.0 skill 或 hook 的人:照上面拿掉

### Added
- `docs/11-security.md`:每把金鑰放哪裡、不能放哪裡、保存什麼資料、公開 repo 的防線、外洩怎麼辦
- `docs/12-local-development.md`:本機跑 Bridge(記憶體存放)與模擬 OpenRouter、接 worker、端到端檢查
- `tools/README.md`:每支工具做什麼、動不動正式資源、需要什麼憑證
- `tools/scan_secrets.py` 與 CI 的 `secrets`:擋金鑰、token、`*.env` 之類的檔案,連 commit 歷史一起查;輸出不顯示命中的內容
- Release 附上 `aigo_bridge_worker.py`、三個開機自動啟動範本與三種客戶端,
  `releases/latest/download/<檔名>` 永遠指向最新版
- README:這個 repo 裡有什麼、依角色從哪裡開始、取得與更新
- docs/04:下載 worker 的指令(macOS／Linux／Windows)、更新 worker
- CI 的 `docs`:所有 Markdown 的相對連結都要存在、每份文件都列在 README

### Changed
- CHANGELOG 每一版固定寫「升級影響」(CONTRIBUTING §4)
- docs/07 §6 升級:改為逐步的升級與退版流程
- `examples/hosted-app-caller`:補前置條件;本機試跑改用 env 檔,不把金鑰放在指令列
- docs/03:`bridge.env` 放 repo 外、設完存進密碼管理工具後可刪
- `tools/provision_tables.py` 的說明更正為五張表

### Removed
- `SKILL.md`、`tools/check_update.py`、`resources/hooks/`,以及 README 的「安裝 Skill」「保持更新」

## [0.2.0] - 2026-09-28

這個 repo 同時是一個 **Agent Skill**:`npx skills add AI-GO-APP/aigo-llm-bridge` 安裝後,
AI agent 會依 `SKILL.md` 協助部署、接上與營運 Bridge,並與 aigo-builder 同樣自動保持最新。
Bridge、worker、客戶端的行為沒有變。

### Added
- `SKILL.md`:Skill 主文件——自我更新(Phase -1)、使用邊界、意圖分流、呼叫端與部署的硬規則、版本對照
- `tools/check_update.py`:與 aigo-builder 相同的更新檢查(3 小時節流、多安裝註冊、發現新版即強制同步);
  狀態檔 `~/.aigo/llm_bridge_update_check.json`,與 aigo-builder 分開
- `resources/hooks/`:Claude Code 與 Codex 的 SessionStart hook 範本
- `tools/version.py`:`VERSION` 為單一來源,同步 Bridge、worker、Python 客戶端的版本常數;
  `--bump` 同時把 CHANGELOG 的 [Unreleased] 改成新版段落
- `CONTRIBUTING.md` 與 PR 範本:分支 → PR → CI → 合併的維護流程、bump 規則、CHANGELOG 寫法
- CI:`skill`(版本一致、SKILL.md 指到的路徑都存在)、`version-bump`(PR 改到發布內容就必須 bump)
- `release` workflow:`main` 上的 `VERSION` 變了就自動建立 tag `vX.Y.Z` 與 GitHub Release

### Changed
- README 改寫:兩種用法(裝成 Skill／直接當套件)、安裝 Skill、保持更新、版本、參與開發
- docs/07 §6 升級:先比對線上 `/healthz` 與 `VERSION`,可用 tag 固定部署版本

### Fixed
- 禁字清單改由 repository secret 提供:原本的 repository variable 會以明文印在公開的 CI 紀錄裡

## [0.1.0] - 2026-09-27

第一個可用版本:本機 Claude Code 與 OpenRouter 並用,由每位使用者自己選優先順序。

### Added
- **`model: "auto"`**:依使用者選的優先順序,在本機(使用者自己的 Claude Code)與雲端(OpenRouter 或 Anthropic)之間主備切換。
  使用者還沒選之前回 `409 priority_required`,**不套任何預設**;只有「換後端可能就會成功」的錯誤才切換,串流只在出字前切換;
  回應以 `x_bridge.priority` / `fallback` 與 `X-Bridge-Priority` / `X-Bridge-Fallback` 註明
- `GET/PUT /bridge/preferences`:依 app × 使用者存優先順序,並回報兩個選項當下是否可用;新表 `biz_bridge_prefs`
- 設定 `BRIDGE_AUTO_LOCAL`、`BRIDGE_AUTO_CLOUD`(auto 的預設候選)、`OPENROUTER_BASE_URL`
- **呼叫端正本 `clients/`**:瀏覽器 `bridge.ts`(優先順序、串流、工單)、Custom App Server Action 用的貼上區塊
  `bridge_block.py`、只用標準函式庫的 Python 客戶端 `aigo_bridge.py`(同步、串流、工單、優先順序、綁定、HMAC)
- `examples/minimal-custom-app`:第一次使用先選優先順序的關卡元件、四支薄殼 action;`examples/hosted-app-caller`(FastAPI)
- `tools/sync_clients.py`:把 `clients/` 同步進 `examples/`,CI 以 `--check` 擋飄移
- `tools/e2e_auto.py` 與 `tools/mock_openrouter.py`:auto 的本機端到端檢查(可控制雲端故障)
- worker 開機自動啟動範本:Windows 工作排程器、macOS launchd、Linux systemd(`worker/autostart/`)
- worker 環境變數 `AIGO_BRIDGE_CLAUDE`(開機常駐時指定 claude 路徑)
- 文件:03 部署、04 worker、05 呼叫端、06 前端串流、07 營運、08 最佳實踐、10 疑難排解;09 補上 auto、偏好、
  綁定與電腦端點、完整錯誤代碼表;01 補上 auto 的本機與平台端到端結果

### Changed
- README 改寫:定位為「本機 Claude Code 與 OpenRouter 並用」,加入快速上手與文件地圖
- 綁定後不算在線,要等 worker `run` 的第一次心跳
- worker 被撤銷時以結束碼 0 結束,開機常駐不會無限重啟
- 範例 action 改為「貼上區塊 + 幾行」的薄殼

### Earlier development (before 0.1.0)
#### Added
- repo 骨架:README、術語表(CONTEXT.md)、架構(docs/01)、使用邊界(docs/02)
- `tools/lint_terms.py`:檢查 repo 內容與 commit 訊息是否出現不該出現在通用套件的字詞;
  清單由 CI 變數或本機 `.banned-terms` 提供,輸出不回顯命中的詞
- CI:禁字檢查、Python 語法檢查、hosted-echo 單元測試
- P1 實測腳本:`spikes/cli-latency`(S1)、`spikes/hosted-echo`(S2–S4 共用的模擬服務)、
  `spikes/custom-app-client`(S2、S3 的 Custom App)、`spikes/cold-poll`(S4)
- `tools/deploy_hosted.py`、`tools/hosted_env.py`、`tools/aigo_api.py`:部署 Hosted App 與安全地更新環境變數
  (先讀現況再合併;共用池租戶不送 `resources`;錯誤訊息不回顯值)
- docs/01 §5:S1、S3 實測數字與由此得出的設計決定;S2 以標頭確認可行並記下 CSP 限制

- **Bridge v1(`hosted/`,P2 進行中)**:OpenAI 相容的 `/v1/chat/completions`、`/v1/responses`、`/v1/models`、
  `/v1/jobs/{id}`;三種後端 `anthropic/*`(官方 SDK,含拒答後備、參數相容處理)、`openrouter/*`(原樣轉送)、
  `local/self`(本人 worker);source 金鑰 / HMAC / 瀏覽器 session token 三種驗證;worker 綁定碼、長輪詢認領、
  租約、逐段回傳、撤銷;平台自建表或記憶體兩種存放;用量帳
- **Worker v1(`worker/aigo_bridge_worker.py`,只用標準函式庫)**:`enroll` / `run` / `status`;
  啟動前確認是本人互動登入的 Claude Code、拒絕長效 token 模式;只領本人工單;`claude -p` 無工具模式;
  串流逐段回傳且在 `message_stop` 即交付;
  帳號 email、同網域 email 與本機路徑的輸出遮罩(串流時只留可能還沒長完的尾巴不送);
  JSON schema 走 `--json-schema`;對話延續(`--session-id` / `--resume`)
- `tools/e2e_local.py`:以官方 openai 客戶端對 Bridge + 真 worker 做端到端檢查
- docs/09 API 參考:轉譯規則、路由(相容既有 OpenRouter 呼叫端的 model 寫法)、錯誤形狀、表設計

- `tools/provision_tables.py`:建立或補齊四張平台自建表(預設只列計畫)
- `examples/minimal-custom-app`:接上 Bridge 的最小 Custom App(連接我的電腦、瀏覽器直連串流、伺服器端同步呼叫),
  附可直接複製的前端客戶端 `src/lib/bridge.ts`
- docs/01 §5:部署在平台上的端到端結果、共用池配額的觀察

#### Changed
- **思考與 effort 不再寫死**:worker 預設不帶任何 thinking / effort 參數;呼叫端以 `reasoning_effort`、
  `reasoning`(OpenRouter)或 `thinking`(Anthropic)逐次指定,Bridge 依模型轉成實際參數,做不到的列在 `X-Bridge-Dropped`
- `local/self:` 後面接受完整模型 ID;回報實際回答的型號
- 同步等待預設改為 280 秒並新增 `X-Bridge-Wait`;anthropic / openrouter 同步呼叫逾時改為轉工單在背景完成(回 202)
- 所有串流在 280 秒主動收尾(`stream_timeout` 事件 + `[DONE]`)
- JSON 模式下拿掉模型多包的程式碼區塊外框
- 自建表預設前綴改為 `biz_bridge_`(平台慣例);查詢鍵在表上的實體名為 `lookup_key`
- owner / caller user 改以平台使用者 id(`ctx.user_id`)識別,不再以 email

#### Fixed
- 綁定時 Bridge 回 500:平台自建表的 number 欄讀回來是字串,存放層現在依 schema 轉型
- 沒有空白的英數輸出被遮罩扣到最後才送:保留量上限改為 64 字元(email 帳號部分的上限)
- worker 超過 240 秒的工作被截斷卻回報完成:上限改為預設 1800 秒(`AIGO_BRIDGE_JOB_TIMEOUT_S`),
  被中止或輸出不完整一律回報失敗
- 實際型號拿不到:`local/*` 串流的最後一個 chunk 與所有非串流回應的本體都帶 `x_bridge`
  (egress 的 `ctx.http.call` 拿不到回應標頭)
- 沒設雲端金鑰時 409 仍建議改用 `anthropic/*`
- `tools/deploy_hosted.py` 失敗時把原因印在最後一行
