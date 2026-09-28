# aigo-llm-bridge

> **English summary** — An OpenAI-compatible LLM gateway for AI GO Custom Apps and Hosted Apps.
> One endpoint serves both **the user's own Claude Code on the user's own computer** and **OpenRouter**.
> Each user chooses which one comes first; the other becomes the automatic fallback.
> The repo is also an **Agent Skill**: install it with `npx skills add AI-GO-APP/aigo-llm-bridge`
> and your coding agent will deploy, wire up and troubleshoot the bridge for you.

讓 AI GO 上的 **Custom App** 與 **Hosted App** 同時使用兩種 LLM 來源,呼叫方式是 OpenAI 相容的:

| 來源 | 誰付費 | 什麼時候可用 |
|---|---|---|
| **本機**:使用者自己電腦上的 Claude Code | 使用者**本人**的 Claude 方案 | 使用者的電腦開著、worker 在執行 |
| **雲端**:OpenRouter(或 Anthropic API) | 組織的金鑰,按量計費 | 隨時 |

呼叫時寫 `model: "auto"`。**每位使用者第一次使用時自己選要優先用哪一個**,另一個自動當備援;
每個回應都註明實際由誰回答、有沒有用到備援。

```
app ──► Bridge ──► 使用者選的優先 ──(不可用)──► 另一個
                    本機 Claude Code   ◄──►   OpenRouter
```

> ⚠️ 本機那一側有明確的使用邊界:**一個人的 Claude Code 只處理那個人自己送出的工作**,
> 不能替其他使用者運算、不能集中成一台共用機器。套件在伺服端強制這一條。
> 啟用前請先讀 [docs/02 · 使用邊界](docs/02-compliance.md)。

## 兩種用法

| 用法 | 適合 | 從哪裡開始 |
|---|---|---|
| **A. 裝成 Skill,讓 AI agent 帶你做** | 用 Claude Code / Codex / Cursor / Antigravity 開發 AI GO app 的人 | [安裝 Skill](#安裝-skill) |
| **B. 直接當套件用** | 想自己照文件一步步部署、或把客戶端複製進既有專案的人 | [快速上手](#快速上手) |

兩者是同一份內容:Skill 的 [`SKILL.md`](SKILL.md) 只是替 agent 整理好「什麼情況讀哪份文件、哪些事不能做」。

## 安裝 Skill

用 [`skills`](https://github.com/vercel-labs/skills) CLI 安裝(會自動偵測 agent 並裝到正確位置):

```bash
npx skills add AI-GO-APP/aigo-llm-bridge
```

指定 agent 或安裝範圍:

```bash
npx skills add AI-GO-APP/aigo-llm-bridge --agent claude-code --scope user
```

<details>
<summary>手動安裝(不使用 CLI)</summary>

直接 clone 到 agent 的 skills 目錄,**保留完整目錄結構**(`SKILL.md` 會指向 `docs/`、`clients/`、`tools/`):

```bash
# Claude Code,所有專案共用
git clone https://github.com/AI-GO-APP/aigo-llm-bridge.git ~/.claude/skills/aigo-llm-bridge

# 其他 agent 的專案內
git clone https://github.com/AI-GO-APP/aigo-llm-bridge.git .agents/skills/aigo-llm-bridge
```

</details>

裝好之後,在 AI IDE 裡直接說要做什麼即可,例如「幫我在這個租戶部署 LLM Bridge」、
「這個 Custom App 要加一個 AI 對話頁」、「使用者一直收到 priority_required」。

**搭配 aigo-builder**:建 app、登入平台、授權 egress、發布這些平台操作由
[aigo-builder skill](https://github.com/AI-GO-APP/aigo-app-builder-skill) 負責;
本 Skill 的部署工具會沿用它的登入與工作區設定(`tools/aigo_api.py`)。兩個都裝最順。

> ⚠️ **不要把金鑰或 `bridge.env` 放進 Skill 安裝目錄**。安裝目錄是 `main` 的鏡像,
> 更新時會被覆蓋。金鑰放在你的工作區、並確認不進版控。

## 快速上手

需要:一個 AI GO 租戶(能建 Hosted App 與自建表)、一把 OpenRouter 金鑰、Python 3.10+。

1. **部署 Bridge**(約 15 分鐘):產生金鑰 → 建五張表 → 部署 → 設環境變數 → 看 `/healthz`。
   逐步說明在 [docs/03](docs/03-deploy-bridge.md)。

   ```bash
   python tools/provision_tables.py --apply
   python tools/deploy_hosted.py --slug <your-bridge> --src hosted --files Dockerfile,requirements.txt,main.py,bridge
   python tools/hosted_env.py --slug <your-bridge> --env-file bridge.env
   curl -s https://<your-bridge>.deploy.ai-go.app/healthz
   ```

2. **接上你的 app**,擇一:
   - Custom App:照 [examples/minimal-custom-app](examples/minimal-custom-app) 建一個,或把
     [`clients/custom-app/bridge_block.py`](clients/custom-app/bridge_block.py) 貼進你的 action、
     [`clients/browser/bridge.ts`](clients/browser/bridge.ts) 放進你的前端。
   - Hosted App 或其他伺服器程式:[`clients/python/aigo_bridge.py`](clients/python/aigo_bridge.py),
     或任何 OpenAI 相容 SDK(只換 base URL 與金鑰,加一個使用者標頭)。範例
     [examples/hosted-app-caller](examples/hosted-app-caller)。

3. **第一次使用時問使用者優先用哪一個**(沒選之前 `auto` 會回 `409 priority_required`):

   ```python
   if bridge.get_priority(user)["priority"] is None:
       ...                                          # 畫面上讓使用者選
   bridge.set_priority(user, "local")               # 或 "cloud"
   reply = bridge.chat([{"role": "user", "content": "你好"}], user=user)
   print(reply.content, reply.served_by, reply.fallback)
   ```

4. **想用本機的使用者**在自己電腦上裝 worker(一個 Python 檔,不需要安裝套件):
   app 內「連接我的電腦」取得綁定碼 → `python aigo_bridge_worker.py enroll ...` → `run`。
   可設開機自動啟動。見 [docs/04](docs/04-worker.md)。

## 文件

| 文件 | 給誰 | 內容 |
|---|---|---|
| [01 · 架構](docs/01-architecture.md) | 想知道為什麼這樣設計 | 元件、每個設計對應的平台限制、全部實測數字 |
| [02 · 使用邊界](docs/02-compliance.md) | **啟用本機前必讀** | 能做與不能做的事,以及程式怎麼強制 |
| [03 · 部署 Bridge](docs/03-deploy-bridge.md) | 租戶管理者 | 金鑰、建表、部署、環境變數總表、配額 |
| [04 · 安裝 worker](docs/04-worker.md) | 想用本機的使用者 | 綁定、執行、開機自動啟動、撤銷 |
| [05 · 呼叫端](docs/05-callers.md) | app 開發者 | `auto` 與優先順序、三種客戶端、同步/非同步/串流怎麼選 |
| [06 · 前端串流](docs/06-frontend-streaming.md) | Custom App 前端開發者 | 直連串流、判斷完整、錯誤對應的畫面文字 |
| [07 · 營運](docs/07-operations.md) | 租戶管理者 | 每天看什麼、配額、金鑰、資料保存、升級 |
| [08 · 最佳實踐](docs/08-best-practices.md) | app 開發者 | thinking、結構化輸出、時間上限、成本 |
| [09 · API 參考](docs/09-api-reference.md) | 需要逐條規格時 | 端點、路由、轉譯規則、錯誤代碼表 |
| [10 · 疑難排解](docs/10-troubleshooting.md) | 出問題時 | 依「看到什麼」查原因與處理 |
| [SKILL.md](SKILL.md) | AI agent | 意圖分流、硬規則、版本對照 |
| [CONTRIBUTING](CONTRIBUTING.md) | 要改這個 repo 的人 | 分支、PR、版本、CHANGELOG 的寫法 |

術語見 [CONTEXT.md](CONTEXT.md),變更見 [CHANGELOG.md](CHANGELOG.md),目前版本見 [VERSION](VERSION)。

## 保持更新

Skill 內含版本標記(`VERSION`)與更新腳本(`tools/check_update.py`),機制與 aigo-builder 相同:
比對本地與 GitHub 上的 `VERSION`;**遠端較新時直接把本機所有已註冊安裝強制同步到遠端 `main`,
不詢問、不保留本地修改**。腳本零相依(只用 Python 標準函式庫),離線或逾時一律靜默略過。

- **頻率**:每次 Skill 觸發時執行(`SKILL.md` 的 Phase -1),或在每次開 session 時由 hook 執行。
  遠端版本抓一次後快取 **3 小時**;同步失敗的安裝 3 小時內不重試;**版本比對每次都做**。
  狀態存在 `~/.aigo/llm_bridge_update_check.json`,與 aigo-builder 的狀態檔分開。
- **強制同步的做法**:git 安裝執行 `git fetch origin main` → `git reset --hard FETCH_HEAD` → `git clean -fd`
  (gitignore 的檔案不動);`npx skills add` 的複製式安裝下載 `main.zip` 鏡像覆蓋
  (`.git`／`.venv`／`.aigo`／`.claude`／`*.env`／`.banned-terms` 例外)。
  **你在安裝目錄裡做的任何修改都會被覆蓋**;要改 Skill 內容請開 PR([CONTRIBUTING](CONTRIBUTING.md))。
- **唯一不碰的是開發用副本**:本地版本高於遠端,或 git 副本不在 `main`／`master` 分支。
- **多安裝同步**:每份安裝執行檢查時會登記自己的路徑;任一份發現新版時,清單裡所有落後的安裝一起同步。
  只認得「至少跑過一次檢查」的安裝。

**Claude Code / Codex(推薦加裝)**:用 SessionStart hook 在 Skill 載入**之前**完成同步,新版當下就生效。
範本在 `resources/hooks/`,把 `<SKILL_DIR>` 換成本機路徑後合併進設定:

| Agent | 設定檔 | 範本 |
|---|---|---|
| Claude Code | `~/.claude/settings.json` 或 `<專案>/.claude/settings.json` | [`claude-code.settings.example.json`](resources/hooks/claude-code.settings.example.json) |
| Codex CLI(>= v0.124.0) | `~/.codex/config.toml` 或 `<repo>/.codex/config.toml` | [`codex.config.example.toml`](resources/hooks/codex.config.example.toml) |

已經裝了 aigo-builder 的 hook 的話,把這支的 command 加進同一個 `SessionStart` 陣列即可。

手動執行:

```bash
python tools/check_update.py               # 檢查並同步;沒動作就沒輸出(macOS/Linux 用 python3)
python tools/check_update.py --force       # 忽略節流
python tools/check_update.py --json        # 機器可讀輸出
python tools/check_update.py --check-only  # 只報告不同步(維護者／CI 用)
```

## 版本

版本號遵循 [SemVer](https://semver.org/),**單一來源是 [`VERSION`](VERSION)**,
由 `tools/version.py` 同步到程式碼常數,CI 檢查四處一致、且每一版在 CHANGELOG 都有段落。
0.x 期間 API 可能變動,每次變動都寫在 [CHANGELOG](CHANGELOG.md),破壞性變更會寫在該版段落的最前面。

一套環境裡看得到三個版本號,正常情況下都應該等於 `VERSION`:

| 元件 | 怎麼看 | 落後時 |
|---|---|---|
| Skill(本 repo 的安裝) | `VERSION` | 自動同步(見上節) |
| 已部署的 Bridge | `curl -s https://<your-bridge>.deploy.ai-go.app/healthz` 的 `version` | 照 [docs/07 §6](docs/07-operations.md) 升級 |
| 使用者電腦上的 worker | `python aigo_bridge_worker.py status` 的 `worker_version` | 換掉 `aigo_bridge_worker.py` 並重啟;舊版仍可用,除非 CHANGELOG 另有說明 |

每一版合併進 `main` 後會自動建立 tag `vX.Y.Z` 與 [GitHub Release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases)。
部署 Bridge 想固定在某一版:`git checkout vX.Y.Z` 之後再跑部署工具。

## 目錄

```
SKILL.md    Skill 主文件(給 AI agent:意圖分流、硬規則、版本對照)
CONTEXT.md  術語表
hosted/     Bridge 本體(部署成 Hosted App)
worker/     使用者電腦上的 worker(單一 Python 檔)與開機自動啟動範本
clients/    三種呼叫端的正本:瀏覽器、Custom App Server Action、Python
examples/   可直接發布的範例:Custom App、Hosted App 呼叫端
tools/      部署、建表、同步範例、版本、更新檢查、禁字檢查等工具
resources/  SessionStart hook 範本(Claude Code、Codex)
docs/       文件
spikes/     設計前的實測腳本(量完的數字寫在 docs/01,腳本保留供重跑)
```

`examples/` 裡的客戶端是 `clients/` 的副本,由 `python tools/sync_clients.py` 同步,CI 會檢查兩者一致。

## 參與開發

流程只有一條:**分支 → PR → CI 全綠 → 合併**,不直接推 `main`。細節見 [CONTRIBUTING.md](CONTRIBUTING.md),重點:

- 改到使用者拿得到的內容,就要 `python tools/version.py --bump patch|minor|major` 並寫 CHANGELOG;
  沒 bump 的變更,已安裝的使用者收不到(CI 的 `version-bump` 會擋)。
- **這是通用套件**:repo 內(含 commit 訊息)不得出現任何特定客戶、租戶、專案或人名。CI 的 `lint-terms` 會擋;
  範例一律用 `<your-tenant>`、`<your-bridge>` 這類佔位。
- 改了 `clients/` 就跑 `python tools/sync_clients.py`。
- 測試:`cd hosted && pytest`(Bridge 與三種客戶端)、`cd worker && pytest tests`、`pytest tools/tests`(Skill 與版本工具)。
- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。

## 授權

[MIT](LICENSE)
