# Changelog

格式參考 [Keep a Changelog](https://keepachangelog.com/),版本號遵循 [SemVer](https://semver.org/)。
0.x 期間 API 可能變動,每次變動都會寫在這裡。

## [Unreleased]

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
