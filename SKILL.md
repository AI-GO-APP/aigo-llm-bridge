---
name: aigo-llm-bridge
description: >
  Use when an AI GO Custom App 或 Hosted App (ai-go.app) 要呼叫 LLM:部署或升級
  aigo-llm-bridge(OpenAI 相容閘道,Hosted App)、把呼叫端接進 Custom App 前端／Server Action
  或 Hosted App、`model: "auto"` 與使用者優先順序(本機 Claude Code ↔ OpenRouter 主備)、
  讓使用者在自己電腦上安裝 worker、營運與配額、或處理 Bridge 的錯誤代碼
  (priority_required、no_worker_for_user、provider_auth、stream_timeout…)。
---

# AI GO LLM Bridge

本 Skill 協助 AI Agent 在 AI GO 上**部署、接上、營運** aigo-llm-bridge:一個 OpenAI 相容的 LLM 閘道,
同一個端點背後有兩種來源——使用者**本人電腦上的 Claude Code**(本機)與組織的 **OpenRouter／Anthropic 金鑰**(雲端)。
每位使用者自己選哪一個優先,另一個自動當備援。支援 Claude Code / Codex / Cursor / Antigravity。

> **術語先讀 `CONTEXT.md`**:Bridge、Provider、`auto`、優先順序、備援、Owner、Source、Caller user、
> Session token 在這裡都有精確意思,混用就會寫錯程式或給錯建議。

## Phase -1:Skill 自我更新(每次觸發時執行,發現新版即強制同步)

> 若已裝 SessionStart hook(見 README「保持更新」),本階段會自動被跳過(節流),不必重複執行。

```bash
python tools/check_update.py     # 在 skill 目錄下執行;macOS / Linux 用 python3
```

- **零相依**——標準函式庫實作,任何專案下都能直接跑。
- **腳本自己動手,不徵詢**:遠端 `VERSION` 比本地新,就把本機所有已註冊安裝**強制同步到遠端 main**
  (git 安裝 `fetch` + `reset --hard` + `clean`;複製式安裝下載 `main.zip` 鏡像覆蓋)。
  你不需要也**不可以**替使用者做「要不要更新」的決定。
- **無輸出 = 沒事**(已是最新、離線、或 3 小時內已失敗過一次),直接往下走。
- **有輸出**,逐行處理:
  - **「已同步」**→ **立刻重新讀取 `SKILL.md` 與相關 `docs/`**,讓新版指令在本回合生效;
    把版本落差與變更摘要**告知**使用者(告知,不是徵詢)。
  - **「失敗」**→ 把原因與腳本印出的手動指令給使用者。若同時有「破壞性變更」警語:
    明確說「不處理會遇到什麼」,之後遇到相關錯誤**優先懷疑版本落差**。
  - **「開發副本,略過」**→ 那份是正在改 skill 的工作區,不用處理也不用提。
- **禁止繞過**:不要為了保住本地修改而跳過本階段或改用 `--check-only`。要改 skill 內容,走 repo 的 PR
  (`CONTRIBUTING.md`);裝在本機的副本只能是遠端 main 的鏡像。

## 使用邊界(任何工作之前,不可協商)

**一個人的 Claude Code,只處理那個人自己送出的工作。** 細節與依據在 `docs/02-compliance.md`,
使用者要啟用本機那一側之前,先請他讀過。以下要求**一律拒絕,並說明原因與替代做法**:

| 要求 | 回應 |
|---|---|
| 讓多人共用一台 worker、把 worker 裝在伺服器／容器／CI | 拒絕。改用雲端:`openrouter/*` 或 `anthropic/*` |
| 用 `claude setup-token` / `CLAUDE_CODE_OAUTH_TOKEN` 跑 worker | 拒絕(worker 本身也會拒絕啟動) |
| 找不到本人 worker 時改派給別人的 worker | 拒絕。`auto` 會改用**同一位使用者**的雲端後端 |
| app 替使用者預設優先順序、跳過選擇畫面 | 拒絕。優先順序只能由使用者本人選(`409 priority_required` 是設計,不是 bug) |
| 排程、無人值守、替系統或多位使用者產生內容 | 不用 `local` 也不用 `auto`,直接指定雲端模型 |

## 意圖分流(先判斷使用者要做哪一件事)

| 意圖 | 誰會這樣問 | 先讀 | 主要工具／檔案 |
|---|---|---|---|
| **部署 Bridge**(租戶第一次導入) | 租戶管理者 | `docs/03-deploy-bridge.md` | `tools/provision_tables.py`、`deploy_hosted.py`、`hosted_env.py` |
| **Custom App 要用 LLM** | app 開發者 | `docs/05-callers.md` §1–3、§5–6 → `docs/06-frontend-streaming.md` | `clients/custom-app/bridge_block.py`、`clients/browser/bridge.ts`、`examples/minimal-custom-app/` |
| **Hosted App／伺服器程式要用 LLM** | app 開發者 | `docs/05-callers.md` §4 | `clients/python/aigo_bridge.py`、`examples/hosted-app-caller/` |
| **在自己電腦上裝 worker** | 終端使用者 | `docs/04-worker.md` | `worker/aigo_bridge_worker.py`、`worker/autostart/` |
| **營運、配額、換金鑰、升級 Bridge** | 租戶管理者 | `docs/07-operations.md` | 同部署工具 |
| **調 thinking、結構化輸出、時間上限、成本** | app 開發者 | `docs/08-best-practices.md` | — |
| **看到錯誤代碼或怪行為** | 任何人 | `docs/10-troubleshooting.md`,再查 `docs/09-api-reference.md` §7 | — |
| **想知道為什麼這樣設計** | 任何人 | `docs/01-architecture.md` | — |

建 app、登入平台、授權 egress、發布 Custom App 這些**平台操作**不在本 Skill 範圍——交給 **aigo-builder** skill。
本 Skill 的部署工具(`tools/aigo_api.py`)會沿用 aigo-builder 的登入與工作區設定。

## 寫呼叫端的硬規則

1. **預設 `model: "auto"`**,第一次使用時處理 `409 priority_required`:顯示選擇卡,
   使用者選完呼叫 `PUT /bridge/preferences`。不要在程式裡替他選(`docs/05-callers.md` §3.2)。
2. **整份複製 `clients/` 的正本,不要自己手寫 HTTP**。Server Action 貼 `bridge_block.py` 的
   「從這裡開始貼」到「到此為止」整段(egress slug 必須是字面字串,所以不能 import);前端整檔複製 `bridge.ts`。
3. **source 金鑰只放伺服器端**(Custom App 的 secrets、Hosted App 的環境變數)。瀏覽器改用
   `bridge_session` action 換來的短效 session token。
4. **使用者身分來自平台**(Server Action 的 `ctx.user_id`),不能讓瀏覽器自己宣稱。
5. **Server Action 有 30 秒硬牆**:同步呼叫帶 `X-Bridge-Wait: 20`,並處理回來的 `pending`(區塊已處理)。
   要逐字顯示就走前端直連串流(`docs/06-frontend-streaming.md`)。
6. **`ctx.http.call` 拿不到回應標頭**:`served_by`、`fallback` 從本體的 `x_bridge` 讀。
7. **瀏覽器直連用 `https://<your-bridge>.deploy.ai-go.app`**,不要用自訂網域(會被 CSP 擋)。
8. 串流沒收到 `[DONE]` 就是不完整;`stream_timeout` 事件帶 `job_id`,用 `/v1/jobs/{id}` 取全文。

## 部署與營運的硬規則

- `AIGO_BASE_URL` 一定是租戶空間 `https://<your-tenant>.ai-go.app`。打 apex 會回跟「密碼錯誤」一模一樣的 401。
- **金鑰檔(`bridge.env`)放在工作區,不要放進 skill 安裝目錄**,也不要進版控。
  安裝目錄是遠端 main 的鏡像,下一次強制同步就可能被清掉或覆蓋。
- `provision_tables.py`、`deploy_hosted.py`、`hosted_env.py` 會改動租戶上的正式資源,**得到使用者同意再執行**:
  建表先跑不帶 `--apply` 的預覽、環境變數先用 `--show` 看現況,把計畫給使用者看。
  `deploy_hosted.py` 的 slug 命中既有 app 就是重新部署、沒命中就是建新 app(子網域全平台共用),執行前先講清楚是哪一種。
- `hosted_env.py` 一律先讀現況再合併,不要改用直接 PUT(省略 `persistent_disk` 會卸載持久碟)。
- 工具的錯誤訊息刻意不回顯金鑰值;你也不要把 `bridge.env` 的內容印進對話。

## 版本對照(協助既有部署時必做)

一套環境裡有三個版本號,都應該跟 `VERSION` 對得上:

| 看哪裡 | 怎麼看 |
|---|---|
| 本 Skill | 本目錄的 `VERSION` |
| 已部署的 Bridge | `curl -s https://<your-bridge>.deploy.ai-go.app/healthz` 的 `version` |
| 使用者的 worker | `python aigo_bridge_worker.py status` 的 `worker_version`;Bridge 端看電腦清單 |

Bridge 比 Skill 舊時,先看 `CHANGELOG.md` 中間各版的 Changed／Fixed,再照 `docs/07-operations.md` §6 升級
(部署前同樣先徵得同意)。舊版 worker 仍可運作,除非 CHANGELOG 另有說明。

## 回報前自我檢查

- 給使用者的程式碼是從 `clients/` 複製的,而不是改寫過的版本?
- 有沒有任何一步讓本機那一側替「不是呼叫者本人」的人運算?
- 所有網址、代號都是使用者自己的值或 `<your-...>` 佔位?本 repo 是通用套件,不寫進任何特定客戶、租戶、專案或人名。
- 動到正式資源的步驟,是否都先給了預覽並取得同意?

## 改 Skill 本身

發現文件錯誤、平台行為變了、或客戶端有 bug:不要只改本機副本(下次同步就會被蓋掉)。
照 `CONTRIBUTING.md` 開分支、bump 版本、補 CHANGELOG、發 PR;合併後所有安裝會在下一次檢查時自動同步。
