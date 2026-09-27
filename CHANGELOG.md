# Changelog

格式參考 [Keep a Changelog](https://keepachangelog.com/),版本號遵循 [SemVer](https://semver.org/)。
0.x 期間 API 可能變動,每次變動都會寫在這裡。

## [Unreleased]

### Added
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
  啟動前確認是本人互動登入的 Claude Code、拒絕長效 token 模式;只領本人工單;`claude -p` 無工具模式、
  haiku 關 thinking、其他模型改用低 effort;串流逐段回傳且在 `message_stop` 即交付;
  帳號 email、同網域 email 與本機路徑的輸出遮罩(串流時只留可能還沒長完的尾巴不送);
  JSON schema 走 `--json-schema`;對話延續(`--session-id` / `--resume`)
- `tools/e2e_local.py`:以官方 openai 客戶端對 Bridge + 真 worker 做端到端檢查
- docs/09 API 參考:轉譯規則、路由(相容既有 OpenRouter 呼叫端的 model 寫法)、錯誤形狀、表設計

- `tools/provision_tables.py`:建立或補齊四張平台自建表(預設只列計畫)

### Changed
- 自建表預設前綴改為 `biz_bridge_`(平台慣例);查詢鍵在表上的實體名為 `lookup_key`
- owner / caller user 改以平台使用者 id(`ctx.user_id`)識別,不再以 email
