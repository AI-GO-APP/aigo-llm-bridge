# hosted-app-caller:從 Hosted App 呼叫 Bridge

一個 FastAPI 小服務,示範伺服器端程式怎麼用 `aigo_bridge.py`(`clients/python/` 的副本,只用標準函式庫)
呼叫 Bridge。原本就在用 OpenAI 相容 SDK 的服務,也可以不用這個客戶端,直接看 docs/05 §4 的寫法。

| 端點 | 作用 |
|---|---|
| `GET /priority` | 讀使用者的優先順序;`priority: null` 代表還沒問過,前端要先讓使用者選 |
| `PUT /priority` | `{"priority": "local"}`(優先用自己電腦的 Claude Code)或 `"cloud"`(優先用 OpenRouter) |
| `POST /ask` | `{"prompt", "wait"?}` 同步回答;等太久回 202 與 `job_id` |
| `GET /jobs/{id}` | 查工單 |
| `POST /ask/stream` | 逐段轉送;最後一個事件 `kind: "done"` 帶 `complete` 與 `meta` |

回應裡的 `served_by`、`priority`、`fallback` 告訴你這次實際由誰回答、有沒有改用備援。

## 前置條件

1. 租戶裡已經部署好 Bridge([docs/03](../../docs/03-deploy-bridge.md)),`/healthz` 正常。
2. Bridge 端替這個服務設好一把 source 金鑰(例 `BRIDGE_KEY__MY_SERVICE`),值存在密碼管理工具裡。
3. 決定誰是上游:這個服務自己**不驗證使用者**,只相信帶了 `INTERNAL_KEY` 的上游(見下節)。
   上游通常是 Custom App 的 Server Action;前端不能直接呼叫這個服務。

金鑰只放在這個 Hosted App 的環境變數,不要寫進程式或 repo([docs/11](../../docs/11-security.md))。

## 身分(一定要換掉的部分)

Bridge 的本機後端只替「使用者本人」運算,所以每個呼叫都要帶使用者 id。`main.py` 的 `current_user()`
是佔位:它只相信帶了正確 `X-Internal-Key` 的上游,並從 `X-User-Id` 取平台使用者 id。
典型的上游是你的 Custom App Server Action(它有 `ctx.user_id`)。**不要讓瀏覽器自己宣稱身分。**

## 部署

```bash
cp ../../clients/python/aigo_bridge.py .     # 已附副本;正本更新後跑 python tools/sync_clients.py
python ../../tools/deploy_hosted.py --slug <your-caller-slug> --src . --files Dockerfile,requirements.txt,main.py,aigo_bridge.py
```

環境變數:`BRIDGE_URL`、`BRIDGE_KEY`(Bridge 發給這個服務的 source 金鑰)、`INTERNAL_KEY`,
選填 `BRIDGE_SOURCE`(給了就改用 HMAC 簽章)。部署與環境變數的做法見 docs/03。

## 本機試跑

金鑰寫在檔案裡,不要放在指令列(shell 歷史會留下來)。檔名取 `*.env` 才會被 gitignore 排除:

```ini
# caller.env
BRIDGE_URL=https://<your-bridge>.deploy.ai-go.app
BRIDGE_KEY=<這個服務的 source 金鑰>
INTERNAL_KEY=local-test
```

```bash
pip install -r requirements.txt
uvicorn main:app --port 8090 --env-file caller.env
curl -s localhost:8090/priority -H "X-Internal-Key: local-test" -H "X-User-Id: <user-id>"
```

不想連正式的 Bridge,改指向本機跑的 Bridge(docs/12)。
