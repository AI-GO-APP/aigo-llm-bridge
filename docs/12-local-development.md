# 12 · 在本機跑 Bridge、測試與端到端檢查

不碰 AI GO 平台、不花雲端費用,在自己電腦上把 Bridge、模擬的 OpenRouter、worker 全部跑起來。
改 Bridge 或客戶端之前、想先看懂行為、或要重現 bug 時用這份。

## 1. 需要什麼

- Python 3.10+(CI 用 3.12)
- `pip install -r hosted/requirements.txt pytest`(端到端檢查另外要 `pip install openai`)
- 要測本機那一側時:已用**自己的帳號**互動登入的 Claude Code(docs/04 §1)

## 2. 單元測試

```bash
cd hosted && python -m pytest -q            # Bridge、三種客戶端、Hosted App 範例
cd worker && python -m pytest tests -q      # worker(只用標準函式庫)
python -m pytest tools/tests -q             # 版本工具、文件連結、機敏資訊掃描
python tools/sync_clients.py --check        # examples/ 的客戶端副本與 clients/ 一致
python tools/version.py --check             # 版本號四處一致
python tools/scan_secrets.py                # 沒有被提交的金鑰
```

以上就是 CI 跑的內容(另加禁字檢查,見 docs/11 §6)。

## 3. 本機跑一個 Bridge

Bridge 用**記憶體存放**(`BRIDGE_STORE=memory`,不需要平台自建表),雲端那一側指向
`tools/mock_openrouter.py`(不連網、不需要真的金鑰,回答固定是 `mock-cloud:<model>`)。

**1)設定檔**。放在 repo 外面,或至少取 `*.env` 的名字(已 gitignore)。金鑰用隨機產生的一次性值:

```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"      # 產生一把,填進下面的 BRIDGE_KEY__DEV
```

```ini
# dev.env
BRIDGE_STORE=memory
BRIDGE_KEY__DEV=<剛產生的值>
OPENROUTER_API_KEY=mock
OPENROUTER_BASE_URL=http://127.0.0.1:8791
BRIDGE_AUTO_CLOUD=openrouter/mock/cloud-model
BRIDGE_PUBLIC_URL=http://127.0.0.1:8790
```

**2)啟動**,兩個視窗:

```bash
# 視窗一,repo 根目錄:模擬 OpenRouter
python -m uvicorn tools.mock_openrouter:app --port 8791

# 視窗二,hosted/ 目錄:Bridge
python -m uvicorn main:app --port 8790 --env-file ../dev.env
```

**3)確認**:

```bash
curl -s localhost:8790/healthz
```

應該看到 `"store": "memory"`、`providers.openrouter: true`、`sources: 1`。

## 4. 手動呼叫

下面的 `$KEY` 是 `dev.env` 裡 `BRIDGE_KEY__DEV` 的值,`dev-user` 是隨便取的使用者 id。

```bash
# 選優先順序(沒選之前 auto 會回 409 priority_required)
curl -s -X PUT localhost:8790/bridge/preferences \
  -H "Authorization: Bearer $KEY" -H "X-Bridge-User: dev-user" \
  -H "Content-Type: application/json" -d '{"priority": "cloud"}'

# 呼叫
curl -s localhost:8790/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H "X-Bridge-User: dev-user" \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "hi"}]}'
```

回應本體的 `x_bridge` 會寫 `served_by: "mock/cloud-model"`、`priority: "cloud"`、`fallback: null`。

模擬雲端故障(測備援):

```bash
curl -s -X POST localhost:8791/_mode -d '{"fail": 503}'     # 之後雲端一律回 503
curl -s -X POST localhost:8791/_mode -d '{"fail": 0}'       # 恢復
```

## 5. 接上本機的 worker

會用**你自己**登入的 Claude Code 跑幾次很短的對話。

```bash
# 產生綁定碼(正式環境由 app 的伺服器端代表登入者產生)
curl -s -X POST localhost:8790/bridge/enrollments \
  -H "Authorization: Bearer $KEY" -H "X-Bridge-User: dev-user"
# → {"code": "ABCD-EFGH", ...}
```

把 worker 的設定放到一個**測試用目錄**,不要蓋掉你平常用的 `~/.aigo-llm-bridge/`:

```bash
export AIGO_BRIDGE_WORKER_HOME=/tmp/bridge-worker-dev          # PowerShell:$env:AIGO_BRIDGE_WORKER_HOME="$env:TEMP\bridge-worker-dev"
python worker/aigo_bridge_worker.py enroll --bridge http://127.0.0.1:8790 --code ABCD-EFGH
python worker/aigo_bridge_worker.py run
```

記憶體存放的 Bridge 重啟後綁定就消失,要重新產生綁定碼。

## 6. 端到端檢查

兩支腳本都用**官方 `openai` 客戶端**打 Bridge,每一項印 `✓ / ✗`,全過結束碼 0。

| 腳本 | 驗什麼 | 前提 |
|---|---|---|
| `tools/e2e_local.py` | `local/self`:同步、串流首段延遲、JSON schema、對話延續、輸出遮罩、別人拿不到你的 worker | worker 已綁定並在跑 |
| `tools/e2e_auto.py` | `auto`:沒選優先順序被拒、兩種優先順序、本機離線改用雲端、雲端故障改用本機(含串流)、請求錯誤不切換、兩邊都失敗 | worker 已綁定(**不用先跑**,腳本會自己啟動與停止);mock 在 8791 |

```bash
python tools/e2e_local.py --base http://127.0.0.1:8790 --key $KEY --user dev-user

python tools/e2e_auto.py --base http://127.0.0.1:8790 --key $KEY --user dev-user \
  --mock http://127.0.0.1:8791 --worker worker/aigo_bridge_worker.py \
  --worker-home /tmp/bridge-worker-dev
```

平台上的端到端(Custom App 執行頁 + Hosted Bridge + 本機 worker)要真的部署,步驟見 docs/03 與
[examples/minimal-custom-app](../examples/minimal-custom-app) 的驗證清單;歷次結果記在 docs/01 §5。

## 7. 用完清掉

- 停掉兩個 uvicorn(Ctrl+C);記憶體存放的資料隨之消失。
- 刪掉測試用的 worker 目錄與 `dev.env`。
