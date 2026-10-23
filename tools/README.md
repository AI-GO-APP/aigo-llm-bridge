# tools:部署、開發與維護工具

都是單一 Python 檔,在 repo 根目錄執行(`python tools/<名稱>.py`)。每支的完整用法寫在檔頭,這裡是總覽。

現行 BYO 的產品入口為 [產品文件](../docs/README.md)。Mac 使用 `install.py` 及 `mac_service.py` 來源安裝／排空／更新／rollback；`verify_macos_console.py --output <隔離目錄>` 執行合成原生 UI 驗證，`verify_macos_upgrade.py --apply` **會更新既有 Mac 服務並用少量訂閱額度做真 HTTPS 合成測試**。後者沿用原 profile，臨時 key 在 RAM，結束撤銷；不部署 Worker、不改電源。見 [Mac 指南](../docs/MACOS-SETUP.md)。下列 Hosted 工具屬歷史產品線。

## 歷史工具

租戶平台部署工具不屬於現行產品安裝流程，也不應由安裝 agent 執行；原始碼只供歷史維護。現行安裝使用 `install.py`、`byo_setup.py` 與 [BYO 指南](../docs/BYO-QUICKSTART.md)。

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
