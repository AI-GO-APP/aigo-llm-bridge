# aigo-llm-bridge

> **English summary** — An OpenAI-compatible LLM gateway for AI GO Custom Apps and Hosted Apps.
> One endpoint serves both **the user's own Claude Code on the user's own computer** and **OpenRouter**.
> Each user chooses which one comes first; the other becomes the automatic fallback.
> This repo is the deployable gateway itself, a per-user desktop worker, ready-to-copy client code,
> and working example apps for the AI GO platform.

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

## 這個 repo 裡有什麼

| 部分 | 是什麼 | 跑在哪裡 |
|---|---|---|
| [`hosted/`](hosted) | **Bridge** 本體(FastAPI) | 部署成租戶裡的一個 AI GO Hosted App |
| [`worker/`](worker) | **worker**:單一 Python 檔,只用標準函式庫 | 每位想用本機的使用者**自己的電腦** |
| [`clients/`](clients) | 三種呼叫端的正本:瀏覽器、Custom App Server Action、Python | 複製進你的 app |
| [`examples/`](examples) | 可直接發布的範例:最小 Custom App、Hosted App 呼叫端 | AI GO 平台 |
| [`tools/`](tools) | 建表、部署、環境變數、本機端到端、維護工具 | 你的電腦 |

## 依角色從哪裡開始

| 你是 | 要做的事 | 讀 |
|---|---|---|
| **租戶管理者** | 部署一個 Bridge 給租戶裡所有 app 共用、管金鑰、看用量 | [03 部署](docs/03-deploy-bridge.md) → [11 機敏資訊](docs/11-security.md) → [07 營運](docs/07-operations.md) |
| **Custom App 開發者** | 讓 app 能呼叫 LLM、逐字顯示、讓使用者選優先順序 | [05 呼叫端](docs/05-callers.md) → [06 前端串流](docs/06-frontend-streaming.md) → [examples/minimal-custom-app](examples/minimal-custom-app) |
| **Hosted App／伺服器程式開發者** | 從自己的服務呼叫 Bridge | [05 呼叫端 §4](docs/05-callers.md) → [examples/hosted-app-caller](examples/hosted-app-caller) |
| **終端使用者** | 讓 app 用自己電腦上的 Claude Code | [04 安裝 worker](docs/04-worker.md) |
| **要改這個 repo 的人** | 修 bug、加功能、改文件 | [12 本機開發](docs/12-local-development.md) → [CONTRIBUTING](CONTRIBUTING.md) |

## 快速上手

需要:一個 AI GO 租戶(能建 Hosted App 與自建表)、一把 OpenRouter 金鑰、Python 3.10+。

1. **部署 Bridge**(約 15 分鐘):產生金鑰 → 建五張表 → 部署 → 設環境變數 → 看 `/healthz`。
   逐步說明在 [docs/03](docs/03-deploy-bridge.md)。

   ```bash
   python tools/provision_tables.py --apply
   python tools/deploy_hosted.py --slug <your-bridge> --src hosted --files Dockerfile,requirements.txt,main.py,bridge
   python tools/hosted_env.py --slug <your-bridge> --env-file <path/to/bridge.env>
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

## 取得與更新

**部署 Bridge 或改程式**:clone 這個 repo,切到要部署的版本。

```bash
git clone https://github.com/AI-GO-APP/aigo-llm-bridge.git
cd aigo-llm-bridge
git checkout vX.Y.Z          # 換成要部署的版本(見 Releases);不切就是 main 上的最新版
```

**只要某一個檔案**(worker、客戶端):每一版的 [GitHub Release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases)
都附上 `aigo_bridge_worker.py`、`bridge.ts`、`bridge_block.py`、`aigo_bridge.py`,永遠指向最新版的下載網址是

```
https://github.com/AI-GO-APP/aigo-llm-bridge/releases/latest/download/<檔名>
```

**更新**:這個 repo 不會自動更新任何東西——線上的 Bridge、使用者電腦上的 worker、複製進 app 的客戶端,
都要由負責的人決定何時換。

1. 看 [CHANGELOG](CHANGELOG.md) 從你現在的版本到新版之間每一版的**升級影響**:
   Bridge 要不要重新部署、要不要補表、worker 要不要換、客戶端要不要重新複製。
2. 照 [docs/07 §6](docs/07-operations.md) 升級。
3. 想收到新版通知:在 GitHub 上 Watch → Custom → Releases。

## 版本

版本號遵循 [SemVer](https://semver.org/),**單一來源是 [`VERSION`](VERSION)**,每一版都有 tag `vX.Y.Z`、
[Release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases) 與 [CHANGELOG](CHANGELOG.md) 段落。
0.x 期間 API 可能變動,破壞性變更會寫在該版段落的最前面。

一套環境裡看得到三個版本號:

| 元件 | 怎麼看 | 落後時 |
|---|---|---|
| 已部署的 Bridge | `curl -s https://<your-bridge>.deploy.ai-go.app/healthz` 的 `version` | 照 [docs/07 §6](docs/07-operations.md) 升級 |
| 使用者電腦上的 worker | `python aigo_bridge_worker.py status` 的 `worker_version`;Bridge 端看 app 的電腦清單 | 換掉 `aigo_bridge_worker.py` 並重啟;舊版仍可用,除非 CHANGELOG 另有說明 |
| 複製進 app 的 Python 客戶端 | 檔內的 `VERSION` 常數 | 重新複製;瀏覽器客戶端與 Server Action 區塊沒有版本常數,以 CHANGELOG 為準 |

## 文件

| 文件 | 給誰 | 內容 |
|---|---|---|
| [01 · 架構](docs/01-architecture.md) | 想知道為什麼這樣設計 | 元件、每個設計對應的平台限制、全部實測數字 |
| [02 · 使用邊界](docs/02-compliance.md) | **啟用本機前必讀** | 能做與不能做的事,以及程式怎麼強制 |
| [03 · 部署 Bridge](docs/03-deploy-bridge.md) | 租戶管理者 | 金鑰、建表、部署、環境變數總表、配額 |
| [04 · 安裝 worker](docs/04-worker.md) | 想用本機的使用者 | 下載、綁定、執行、開機自動啟動、撤銷 |
| [05 · 呼叫端](docs/05-callers.md) | app 開發者 | `auto` 與優先順序、三種客戶端、同步/非同步/串流怎麼選 |
| [06 · 前端串流](docs/06-frontend-streaming.md) | Custom App 前端開發者 | 直連串流、判斷完整、錯誤對應的畫面文字 |
| [07 · 營運](docs/07-operations.md) | 租戶管理者 | 每天看什麼、配額、金鑰、資料保存、升級 |
| [08 · 最佳實踐](docs/08-best-practices.md) | app 開發者 | thinking、結構化輸出、時間上限、成本 |
| [09 · API 參考](docs/09-api-reference.md) | 需要逐條規格時 | 端點、路由、轉譯規則、錯誤代碼表 |
| [10 · 疑難排解](docs/10-troubleshooting.md) | 出問題時 | 依「看到什麼」查原因與處理 |
| [11 · 機敏資訊與安全](docs/11-security.md) | 所有人 | 每把金鑰放哪裡、不能放哪裡、保存什麼資料、外洩怎麼辦 |
| [12 · 本機開發](docs/12-local-development.md) | 要改程式或重現問題的人 | 本機跑 Bridge、模擬雲端、接 worker、端到端檢查 |
| [tools/README](tools/README.md) | 部署者、維護者 | 每支工具做什麼、動不動正式資源 |
| [CONTRIBUTING](CONTRIBUTING.md) | 要改這個 repo 的人 | 分支、PR、版本、CHANGELOG 的寫法 |

術語見 [CONTEXT.md](CONTEXT.md)。

## 目錄

```
hosted/     Bridge 本體(部署成 Hosted App)
worker/     使用者電腦上的 worker(單一 Python 檔)與開機自動啟動範本
clients/    三種呼叫端的正本:瀏覽器、Custom App Server Action、Python
examples/   可直接發布的範例:Custom App、Hosted App 呼叫端
tools/      部署、建表、本機端到端、版本、禁字與機敏資訊檢查
docs/       文件
spikes/     設計前的實測腳本(量完的數字寫在 docs/01,腳本保留供重跑)
```

`examples/` 裡的客戶端是 `clients/` 的副本,由 `python tools/sync_clients.py` 同步,CI 會檢查兩者一致。

## 參與開發

流程只有一條:**分支 → PR → CI 全綠 → 合併**,不直接推 `main`。細節見 [CONTRIBUTING.md](CONTRIBUTING.md),重點:

- 改到部署者或使用者拿得到的內容,就要 `python tools/version.py --bump patch|minor|major`,
  並在 CHANGELOG 寫清楚**升級影響**。
- **這是公開的通用套件**:repo 內(含 commit 訊息與作者名)不得出現任何特定客戶、租戶、專案或人名,
  也不得有任何金鑰。CI 的 `lint-terms` 與 `secrets` 會擋;範例一律用 `<your-tenant>`、`<your-bridge>` 這類佔位。
- 改了 `clients/` 就跑 `python tools/sync_clients.py`。
- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。

## 授權

[MIT](LICENSE)
