# 07 · 營運

## 1. 每天看什麼

| 看什麼 | 在哪裡 | 正常樣子 |
|---|---|---|
| Bridge 活著、設定對 | `GET /healthz` | `ok: true`、`store: aigo`、有金鑰的後端為 `true`、`sources` 等於呼叫端數 |
| 每次呼叫的結果 | 自建表 `biz_bridge_usage` | `status` 多為 `ok`;`fallback` 代表優先的那個失敗、改用了備援 |
| 誰的電腦在線 | 自建表 `biz_bridge_workers` | `status = active`、`last_seen_ts` 在 90 秒內 |
| 卡住的工單 | 自建表 `biz_bridge_jobs` | 沒有長時間停在 `pending` / `leased` 的列 |
| 使用者的選擇 | 自建表 `biz_bridge_prefs` | 每個 app × 使用者一列 |

`biz_bridge_usage` 常用的切法:

- **備援比例**:`status = fallback` 的列數 ÷ 總列數。偏高時看 `model` 欄是哪一側在失敗
  (本機側多半是使用者電腦沒開;雲端側看 `http_status` 是限流還是 5xx)。
- **成本**:`provider = openrouter` 的 `cost_usd` 加總是組織的雲端支出;`provider = local` 的成本記的是
  Claude Code 回報的等值金額,實際由使用者自己的方案支付。
- **慢**:`duration_ms` 高的列,對照 `model` 與是否開著 thinking。

## 2. 配額與縮到零

- Bridge 維持冷啟動模式(`always_on=false`)。有 worker 在線就不會縮到零;全部下線一段時間(實測至少 15 分鐘)後才縮。
- 共用池租戶:每個執行個體的記憶體上限是平台常數(約 1.9 GB),部署時新舊兩個同時存在。
  部署失敗顯示 `exceeded quota` 時,等其他 app 縮下來再部署(docs/03 §7)。
- Custom App 的 action 回 503「App runner 暫時不可用」而且帶 `quota_hint`:租戶配額滿了,不是程式問題。

## 3. 金鑰

| 金鑰 | 換的方法 | 影響 |
|---|---|---|
| source 金鑰 `BRIDGE_KEY__<SOURCE>` | 改 Bridge 環境變數 → 更新該 app 的 secret | 那個 app 在兩邊都更新前會 401 |
| `BRIDGE_SESSION_SECRET` | 改 Bridge 環境變數 | 所有瀏覽器 token 失效;使用者重新整理即可 |
| `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` | 改 Bridge 環境變數 | 無 |
| worker 的設備鑰匙 | 使用者在 app 撤銷後重新綁定 | 只影響那台電腦 |

金鑰外洩時先換,再查 `biz_bridge_usage` 那段時間 `source` 的呼叫量。
每把金鑰該放在哪裡、絕不能出現在哪裡,見 [docs/11](11-security.md)。

## 4. 資料保存

- 提示與回應原文**預設不長期保存**。本機工單的提示在完成或失敗時立即清除;`BRIDGE_STORE_PROMPTS=1` 才保存(只在除錯時開)。
- `biz_bridge_usage` 只存 token、成本、耗時、結果,不存內容。會一直累積,依組織政策定期清理
  (`DELETE /api/v1/open/data-center/tables/biz_bridge_usage/records/{id}`,或在資料中心介面操作)。
- 已過期的綁定碼(`biz_bridge_enrollments`)與完成的工單(`biz_bridge_jobs`)可以定期清掉;Bridge 不依賴舊資料。

## 5. 事件處理

| 症狀 | 先看 | 常見原因 |
|---|---|---|
| 所有呼叫 503 `not_configured` | `/healthz` 的 `sources` | 環境變數沒設或部署後被清掉 |
| 所有呼叫 503 `store_*` | 平台資料中心 | 表不存在、欄位缺、每分鐘 600 次額度用完 |
| 雲端側全部 502 `provider_auth` | Bridge 的 OpenRouter 金鑰 | 金鑰失效或被撤 |
| 本機側全部 409 | 使用者的 worker | 大家的電腦都沒開(例如假日);`auto` 會自動改用雲端 |
| 串流常到 280 秒 | 哪個模型、有沒有 thinking | 回答太長;改用非同步或拆小 |
| 部署失敗 `exceeded quota` | 租戶配額 | docs/03 §7 |

更細的對照表見 [10 · 疑難排解](10-troubleshooting.md)。

## 6. 升級

沒有任何東西會自動更新:線上的 Bridge、使用者的 worker、複製進 app 的客戶端,都由負責的人決定何時換。
想收到新版通知,在 GitHub 上 Watch → Custom → Releases。

先確認差多少:`curl -s https://<your-bridge>.deploy.ai-go.app/healthz` 的 `version` 是線上的 Bridge,
[Releases](https://github.com/AI-GO-APP/aigo-llm-bridge/releases) 最上面是最新版。

1. 看 [CHANGELOG](../CHANGELOG.md) 從線上版本到目標版本之間**每一版**的「升級影響」;有「破壞性」字樣的先讀。
2. 取得要部署的版本:`git fetch --tags && git checkout vX.Y.Z`。
3. 有新表或新欄位時先跑 `python tools/provision_tables.py`(預覽)再加 `--apply`(只補缺的,不動既有資料)。
4. 有新的環境變數時,寫一個只含新 key 的檔案跑 `hosted_env.py`(只合併你給的 key)。
5. 部署 Bridge(`deploy_hosted.py`),再看一次 `/healthz` 的 `version`。
6. worker 有新版時,請使用者照 docs/04 §5 更新。舊版 worker 仍可運作,除非 CHANGELOG 另有說明。
7. 客戶端(`bridge.ts`、`bridge_block.py`、`aigo_bridge.py`)有變動時,各 app 的開發者重新複製並發布。

退版:`git checkout` 上一版再部署。`provision_tables.py` 只新增表與欄位、從不刪除,所以通常不必動表;
CHANGELOG 若註明某一版不能退,照那一版的說明做。
