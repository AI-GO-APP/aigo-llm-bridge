# aigo-llm-bridge

> **English summary** — An OpenAI-compatible LLM gateway for AI GO Custom Apps and Hosted Apps.
> One endpoint serves both **the user's own Claude Code on the user's own computer** and **OpenRouter**.
> Each user chooses which one comes first; the other becomes the automatic fallback.

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

術語見 [CONTEXT.md](CONTEXT.md),變更見 [CHANGELOG.md](CHANGELOG.md),目前版本見 [VERSION](VERSION)。

## 目錄

```
hosted/     Bridge 本體(部署成 Hosted App)
worker/     使用者電腦上的 worker(單一 Python 檔)與開機自動啟動範本
clients/    三種呼叫端的正本:瀏覽器、Custom App Server Action、Python
examples/   可直接發布的範例:Custom App、Hosted App 呼叫端
tools/      部署、建表、同步範例、禁字檢查等工具
docs/       文件
spikes/     設計前的實測腳本(量完的數字寫在 docs/01,腳本保留供重跑)
```

`examples/` 裡的客戶端是 `clients/` 的副本,由 `python tools/sync_clients.py` 同步,CI 會檢查兩者一致。

## 參與開發

- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。
- **這是通用套件**:repo 內不得出現任何特定客戶、租戶、專案或人名。CI 的 `lint-terms` 會擋;
  範例一律用 `<your-tenant>`、`<your-bridge>` 這類佔位。
- 改了 `clients/` 就跑 `python tools/sync_clients.py`。
- 測試:`cd hosted && pytest`(Bridge 與三種客戶端)、`cd worker && pytest`。

## 授權

[MIT](LICENSE)
