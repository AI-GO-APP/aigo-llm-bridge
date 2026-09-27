# 03 · 部署 Bridge

Bridge 是一個 AI GO Hosted App。一個租戶部署一個,給這個租戶裡所有要用 LLM 的 app 共用。
全程約 15 分鐘;下面每一步都有「做完怎麼確認」。

## 0. 先決定兩件事

| 決定 | 選項 | 影響 |
|---|---|---|
| 雲端那一側用什麼 | OpenRouter(建議)、Anthropic API、或都不設 | 不設 = 只有本機;`auto` 沒有雲端備援 |
| `auto` 的兩個預設候選 | 本機:`local/self` 或 `local/self:<模型>`;雲端:例 `openrouter/anthropic/claude-sonnet-4.5` | 呼叫端沒帶 `models` 時用這兩個 |

「優先用哪一個」**不在這裡決定**:那是每位使用者第一次使用時自己選的(docs/05 §3)。

## 1. 需要的權限與工具

- 租戶帳號要能建 Hosted App,以及建自建表(`datacenter.schema_write`)。沒有建表權限的話,
  `tools/provision_tables.py` 會印出完整規格,請租戶管理員照著建。
- 本機:Python 3.10+、`pip install httpx`(工具用)。
- 平台憑證二選一:
  - 環境變數 `AIGO_BASE_URL=https://<your-tenant>.ai-go.app` 與 `AIGO_TOKEN=<access token>`
  - 或已設定好的 aigo-builder skill 工作區:`AIGO_WORKSPACE=<含 .aigo/config.json 的目錄>`

> `AIGO_BASE_URL` 一定要是**租戶空間**網址。打 `https://ai-go.app` 會回一個跟「密碼錯誤」長得一樣的 401。

## 2. 產生金鑰

每個會呼叫 Bridge 的 app 一把 source 金鑰,名稱用大寫英數底線。先寫在一個**不進版控**的檔案裡:

```bash
python - <<'EOF' > bridge.env
import secrets
for source in ("SALES_APP", "SUPPORT_APP"):          # 換成你的 app 代號
    print(f"BRIDGE_KEY__{source}={secrets.token_urlsafe(32)}")
print(f"BRIDGE_SESSION_SECRET={secrets.token_urlsafe(32)}")
EOF
```

再把雲端與 `auto` 的設定加進同一個檔案:

```ini
OPENROUTER_API_KEY=sk-or-...
BRIDGE_AUTO_LOCAL=local/self
BRIDGE_AUTO_CLOUD=openrouter/anthropic/claude-sonnet-4.5
```

## 3. 建資料表

```bash
python tools/provision_tables.py            # 只列計畫,不動手
python tools/provision_tables.py --apply    # 建立五張表(或補上缺的欄位)
```

會建 `biz_bridge_jobs`、`workers`、`enrollments`、`usage`、`prefs`(docs/09 §8)。
表名是租戶級、實體名建立後不能改;前綴要換請同時設 `BRIDGE_TABLE_PREFIX`。

**確認**:再跑一次不帶 `--apply`,應該顯示五張表都已存在、沒有缺欄。

## 4. 部署

```bash
python tools/deploy_hosted.py --slug <your-bridge> --src hosted \
  --files Dockerfile,requirements.txt,main.py,bridge
python tools/hosted_env.py --slug <your-bridge> --env-file bridge.env
```

- 第一次會建立 Hosted App(平台預設 `public`),之後同一個 slug 是新的一次部署。
- **slug 取好再建**:刪除過的 Hosted App 會永久保留它的 slug,之後不能再用。先用一次性的名字試,正式的名字只建一次。
- **必須是 `public`**:`internal` 的 Hosted App 拿不到呼叫者身分,Bridge 靠自己的金鑰與簽章驗證。
- **網址必須留在 `*.ai-go.app`**:Custom App 執行頁的 CSP 只允許這個範圍,綁自訂網域後瀏覽器直連會被擋。
- **維持冷啟動模式(`always_on=false`)**:平台預設就是,不要開常駐。有 worker 在線時 Bridge 本來就不會縮到零
  (worker 每 25 秒輪詢一次);所有人都下線後才縮到零,這正是要的。
- `hosted_env.py` 會先讀現況再合併,只改你給的 key,常駐設定與其他變數原樣保留;值不會印出來。

**確認**:

```bash
curl -s https://<your-bridge>.deploy.ai-go.app/healthz
```

應該看到 `"store": "aigo"`、`providers` 裡你設了金鑰的後端為 `true`、`sources` 等於你設的 app 數。

## 5. 環境變數總表

| 變數 | 必要 | 預設 | 用途 |
|---|---|---|---|
| `BRIDGE_KEY__<SOURCE>` | ✅ | — | 每個呼叫端 app 一把 |
| `BRIDGE_SESSION_SECRET` | 建議 | 由所有 source 金鑰衍生 | 簽瀏覽器用的 session token;沒設的話換任何 source 金鑰都會讓既有 token 失效 |
| `OPENROUTER_API_KEY` | 雲端用 OpenRouter 時 | — | `openrouter/*` 與沒有 Anthropic 金鑰時的 `anthropic/*` |
| `ANTHROPIC_API_KEY` | 選填 | — | `anthropic/*` 直連 Anthropic |
| `BRIDGE_AUTO_LOCAL` | 選填 | `local/self` | `auto` 的本機候選 |
| `BRIDGE_AUTO_CLOUD` | 選填 | 空 | `auto` 的雲端候選;空 = 沒有雲端備援 |
| `BRIDGE_DEFAULT_MODEL` | 選填 | 空 | 沒帶 `model` 的請求用哪個 |
| `BRIDGE_SYNC_TIMEOUT` | 選填 | `280` | 同步呼叫最多等幾秒(上限 280) |
| `BRIDGE_PUBLIC_URL` | 選填 | 由 slug 推 | 對外網址(寫進綁定碼回應) |
| `BRIDGE_TABLE_PREFIX` | 選填 | `biz_bridge_` | 自建表前綴 |
| `BRIDGE_STORE_PROMPTS` | 選填 | 關 | `1` = 長期保存提示與回應原文(除錯用) |
| `BRIDGE_ANTHROPIC_FALLBACKS` | 選填 | 開 | `off` = 不帶 Anthropic 的拒答後備 |
| `BRIDGE_STORE` | 選填 | `aigo` | `memory` = 不用平台表(只給本機開發) |
| `OPENROUTER_BASE_URL` | 選填 | `https://openrouter.ai/api/v1` | 測試或代理用 |
| `AIGO_PLATFORM_API_URL`、`AIGO_API_TOKEN`、`AIGO_HOSTED_APP_SLUG` | 平台注入 | — | 不用自己設 |

## 6. 接上呼叫端

| 呼叫端 | 要做的事 |
|---|---|
| Custom App | Builder「外部服務」建 slug `llm-bridge`(base_url = Bridge 網址、timeout 30000 毫秒)並授權給 app;secrets 設 `BRIDGE_KEY`、`BRIDGE_PUBLIC_URL`。程式見 [examples/minimal-custom-app](../examples/minimal-custom-app) |
| Hosted App | 環境變數設 `BRIDGE_URL`、`BRIDGE_KEY`(可再加 `BRIDGE_SOURCE` 改用簽章)。程式見 [examples/hosted-app-caller](../examples/hosted-app-caller) |

外部服務也可以用 API 建:`POST /api/v1/builder/apps/{app_id}/egress-services`
`{"name", "slug": "llm-bridge", "base_url", "auth_type": "none", "timeout_ms": 30000}`,
再 `PUT /api/v1/builder/apps/{app_id}/authorized-egress-services` `{"services": [{"service_id"}]}`
(這個 PUT 是**整份替換**,要連同 app 原本授權的服務一起送)。

## 7. 共用池租戶的配額

共用池租戶(沒有專屬節點)每個 Hosted App 執行個體的記憶體上限是平台常數,不能自己調低
(`runtime-settings.resources` 回 403 `RESOURCES_REQUIRE_DEDICATED_NODES`)。實測這個常數約 1.9 GB,
而租戶總量常見是 8 GB:

- **部署時新舊兩個執行個體會同時存在**。租戶忙的時候部署會失敗(`exceeded quota: aigo-quota`),
  等其他 app 縮下來再部署;`deploy_hosted.py` 會在最後一行印出失敗原因。
- 同一段時間裡 Custom App 的 action 可能回 503「App runner 暫時不可用」,回應帶 `quota_hint`。那不是程式問題。
- 有 worker 在線時 Bridge 不會縮到零,等於長期佔一個執行個體的配額。這是冷啟動模式的正常語意。

## 8. 更新與移除

- **更新**:同一個 slug 再跑一次 `deploy_hosted.py`。環境變數不受影響。
- **換金鑰**:改 `bridge.env` 再跑 `hosted_env.py`,然後同步更新呼叫端的 secret。換 `BRIDGE_SESSION_SECRET` 會讓所有瀏覽器 token 失效,使用者重新整理頁面即可。
- **移除**:刪 Hosted App(`DELETE /api/v1/hosted-apps/{id}`),再刪五張表
  (`GET /api/v1/data-center/tables/{表名}/impact` 看影響,`DELETE ...?confirm={表名}`)。
  使用者電腦上的 worker 會在下一次輪詢時連不上;請他們自行移除開機常駐(docs/04 §5)。
