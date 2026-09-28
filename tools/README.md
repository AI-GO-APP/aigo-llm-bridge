# tools:部署、開發與維護工具

都是單一 Python 檔,在 repo 根目錄執行(`python tools/<名稱>.py`)。每支的完整用法寫在檔頭,這裡是總覽。

## 部署到 AI GO(會動到租戶上的正式資源)

| 工具 | 做什麼 | 動到什麼 | 先看再做 |
|---|---|---|---|
| [`provision_tables.py`](provision_tables.py) | 建立或補齊 Bridge 的五張自建表 | 租戶資料中心(表是**租戶級**,實體名建立後不能改) | 不帶 `--apply` 只列計畫 |
| [`deploy_hosted.py`](deploy_hosted.py) | 把目錄打包部署成 Hosted App;第一次建立,之後是新的一次部署 | Hosted App(slug 全平台共用,刪過的 slug 不能再用) | 會列出打包清單並確認有 Dockerfile |
| [`hosted_env.py`](hosted_env.py) | 設 Hosted App 的環境變數:先讀現況,只合併你給的 key | Hosted App 執行期設定 | `--show` 只列出現有的 key,不寫入 |
| [`aigo_api.py`](aigo_api.py) | 上面三支共用的平台連線層,不直接執行 | — | — |

**平台憑證**(擇一):

- 環境變數 `AIGO_BASE_URL=https://<your-tenant>.ai-go.app` 與 `AIGO_TOKEN`
- 已設定好的 [aigo-builder](https://github.com/AI-GO-APP/aigo-app-builder-skill) 工作區:沿用它的登入與 token 快取;
  工作區目錄用 `AIGO_WORKSPACE` 指定(預設目前目錄),aigo-builder 腳本位置用 `AIGO_SKILL_SCRIPTS` 指定
  (預設 `~/.claude/skills/aigo-builder/scripts`)

`AIGO_BASE_URL` 一定是租戶空間網址;打 apex `https://ai-go.app` 會回一個跟「密碼錯誤」一模一樣的 401。
三支工具的輸出都**不印金鑰值**;金鑰放哪裡見 [docs/11](../docs/11-security.md)。完整部署流程見 [docs/03](../docs/03-deploy-bridge.md)。

## 本機開發與端到端

| 工具 | 做什麼 |
|---|---|
| [`mock_openrouter.py`](mock_openrouter.py) | 模擬 OpenRouter(不連網、不需要金鑰);`POST /_mode {"fail": 503}` 讓它故障 |
| [`e2e_local.py`](e2e_local.py) | 用官方 `openai` 客戶端對執行中的 Bridge 檢查 `local/self` |
| [`e2e_auto.py`](e2e_auto.py) | 檢查 `auto` 的主備切換(會自己啟停 worker、控制 mock 故障) |

怎麼把這些跑起來見 [docs/12](../docs/12-local-development.md)。

## 維護這個 repo

| 工具 | 做什麼 | CI |
|---|---|---|
| [`sync_clients.py`](sync_clients.py) | 把 `clients/` 的正本同步進 `examples/` | `--check` 擋飄移 |
| [`version.py`](version.py) | `VERSION` 是單一來源;`--bump` 同步三個版本常數與 CHANGELOG,`--check` 檢查一致,`--notes` 印出這一版的變更 | `docs`、`version-bump`、`release` |
| [`lint_terms.py`](lint_terms.py) | 擋特定客戶、租戶、專案或人名(含 commit 訊息與作者名);清單來自 secret 或本機 `.banned-terms` | `lint-terms` |
| [`scan_secrets.py`](scan_secrets.py) | 擋被提交的金鑰、token 與 `*.env` 之類的檔案;`--history` 連所有 commit 一起查 | `secrets` |

後兩支的輸出都**不印出命中的內容**,只印位置——這是公開 repo,CI 紀錄是公開的。
工具本身的測試在 [`tests/`](tests)。流程規則見 [CONTRIBUTING](../CONTRIBUTING.md)。
