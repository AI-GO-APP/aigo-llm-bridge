# 實體 Mac source 安裝與 Codex 訂閱驗收（2026-10-22）

此紀錄僅適用本次 Apple Silicon 實機；不是 macOS 通用 release、DMG 或原生 UI 的驗收宣告。沒有修改 AI EA 程式、Windows Worker、裝置資料或 client key。

本輪 source 候選版號為 `0.6.6-mac.1`；依 repo 版本閘門增加版號，未建立 tag 或發布安裝包。

## 來源、環境與安裝

- Repo：`AI-GO-APP/aigo-llm-bridge`。開始時重新 fetch，main／v0.6.5 均為 `0354fbb9feb821f496db8ed5586c775db8446564`；保留原 `feat/macos-installer`，工作區原先乾淨。
- 本輪分支：`codex/mac-physical-acceptance`；實作 commit：`3cfe69f42ed8352d2cce1cadababd79e6e1d8da4`。最後安裝來源以 `source-install.json.source_commit` 為準，包含本輪文件 commit。
- macOS 26.2（25C56）、arm64；Python 3.12.0、Node 22.14.0；Codex CLI 0.163.0-alpha.11，沿用既有 ChatGPT 訂閱登入。
- 正式執行的程式位於 `~/Library/Application Support/AIGO LLM Bridge/versions/`，不是 checkout。專用 Python 為同根的 `runtime/bin/python`，資料是 `data/`，穩定入口是 `Bridge.command`／`Bridge.pyw`。app 的完整路徑每次從 `source-install.json` 讀取。
- 鎖定執行依賴：jsonschema 4.26.0、certifi 2026.2.25。驗收使用此安裝 venv 的 pytest 8.4.2。
- 裝置 ID：`本機驗收 profile（UUID 僅保留本機報告）`；本機推論僅 listen `127.0.0.1:8920`。管理服務另用 loopback 隨機埠，從 Bridge.command 開啟，公網不暴露管理 API。
- LaunchAgent：`~/Library/LaunchAgents/org.aigo.llm-bridge.<profile-hash>.plist`；以使用者 GUI 登入後啟動，stdout/stderr 指向 `/dev/null`，異常退出可由 launchd 重啟。

## 本輪改動

SQLite／WAL／SHM 為 0600、data 根為 0700；裝置配對 secret 存登入 Keychain，active／pending 分開，沒有明文 fallback。LaunchAgent 經穩定 manifest launcher 跟隨更新；新增此安裝專屬的 start／stop／restart／rollback CLI。安裝保留舊版本與 previous manifest，記來源 commit。

Codex 使用獨立 app-server 子程序、空暫存 cwd、ephemeral thread、read-only sandbox、never approval。停用主機 shell、MCP、hooks、plugins、browser、code mode 等工具，history persistence 為 none；不改個人全域 Codex 設定或登入。第三方工具只轉為 schema 驗證過的提案，不在 Mac 執行。另保存已回報的 cache／reasoning token metadata，方便與成本核對。

首次部署曾遇 secret 更新後 edge 未使用最新程式；保留 pending 憑證重部署後配對成功。helper 現在也於首次 secret 寫入後重新發布相同裝置的程式，再檢查公開配對，避免以替換裝置或換網址處理。

## HTTPS 與模型

- Cloud registry origin：`https://YOUR-MAC-WORKER.workers.dev`
- OpenRouter 相容 client base URL：`https://YOUR-MAC-WORKER.workers.dev/api/v1`
- 主模型：`openai/gpt-6.1-sol`；小模型：`openai/gpt-6-luna`。
- Cloud 專用長效 key ID：`僅保留本機交付報告`；非敏感 prefix：`僅保留本機交付報告`；Codex scope、60 rpm。完整值已直接經 stdin 注入可信 Supabase secret `AIEA_BRIDGE_KEY_MAC_PRIMARY`；保留有效，不放聊天、repo、報告或 CI。

獨立第三方服務請另建自己的 key，不共用 Cloud 服務 secret。將 key 放服務端 `LLM_BRIDGE_KEY`；不置於瀏覽器或前端 bundle。

```sh
export LLM_BRIDGE_BASE_URL='https://YOUR-MAC-WORKER.workers.dev/api/v1'
# LLM_BRIDGE_KEY 由可信 secret 管道注入；下列程式不將 KEY 放進 argv 或檔案。
python3 - <<'PYTHON'
import json, os, urllib.request
base = os.environ['LLM_BRIDGE_BASE_URL'].rstrip('/')
headers = {'Authorization': 'Bearer ' + os.environ['LLM_BRIDGE_KEY'],
           'User-Agent': 'llm-bridge-client/1.0', 'Content-Type': 'application/json'}
chat = {'model':'openai/gpt-6.1-sol', 'messages':[{'role':'user','content':'Reply OK.'}], 'stream':False}
for route, body in [('/models', None), ('/chat/completions', chat)]:
    request = urllib.request.Request(base + route, headers=headers,
        data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(request, timeout=100) as response:
        print(json.load(response))
PYTHON
```

給其他 AI IDE／Web IDE 的標準訊息：設定 Chat Completions base URL 為上述 `/api/v1`，從服務端 secret 讀取 `LLM_BRIDGE_KEY`，先 GET models，再 POST 非串流 chat。timeout 100 秒、停用自動 HTTP 重試。只傳已支援的參數；temperature、max_tokens、stream:true 等會明確拒絕。可用 tools／tool_choice／完整 tool result 歷史，提案由消費端依原權限判斷，Bridge 不執行。需要原生 Responses、串流或 Anthropic 協定的 IDE agent 尚不相容。詳見 [第三方串接](THIRD-PARTY-INTEGRATION.md)。

## 實機檢查

本機經公開 HTTPS 的主驗收 37 項、恢復／rollback 補驗 6 項，共 43 項通過。原始 runtime request／response 不寫檔，只保留 allowlist metadata；本機完整 metadata 位於安裝根的 `mac-acceptance-metadata.json`、`mac-recovery-metadata.json`。

| 項目 | 結果 |
|---|---|
| 公開 GET models、preflight、主／小模型文字 | 真實 Worker → Mac → ChatGPT 訂閱 Codex 成功；models 與實際 CLI 列表交叉核對 |
| 多輪、json_object、嚴格 json_schema | 真實模型語意／格式驗證通過 |
| 131 tools、named／required／auto／none、工具結果接續 | 通過；沒有執行提案的主機動作 |
| 不支援參數 | temperature、max_tokens、top_p、stream:true、provider.order 均 structured 400 unsupported_parameter |
| 用量、牌價與 LOG | input／output／cache／reasoning 回報與 LOG 核對，Decimal 獨立核算 cost；沒有精確數值時 fail closed |
| UUID／receipt | 同 generation 不再推論；不同內容相同 UUID 為 409；重啟後 receipt 僅保留 billing metadata，舊請求 409 不重播 |
| 逾時與恢復 | deadline 408 有 terminated 狀態，下一筆真實推論成功 |
| key／LOG | 建立、provider scope、輪替、舊 key 401、撤銷、查詢與清理通過；測試 key 全部撤銷 |
| 程式重啟、source 更新、同帳戶重部署 | 原 device／URL／同一仍有效 key 都維持，且逐次完成真實推論 |
| 供應端離線／恢復 | 停止本次 Bridge、heartbeat 失效回 503；暫停本次程序後恢復，同一程序重連並真實推論 |
| LaunchAgent／回復上一版 | 實際 bootstrap、stop、restart、source 更新、rollback 舊 app、同 key 再推論，最後恢復新版 |
| Keychain | 實際配對讀寫成功；另建隔離測試 Keychain，鎖住時拒絕讀取、解鎖後值一致，測完刪除；未鎖定使用者登入 Keychain |
| 隱私 | Bridge data 無合成 payload／完整 key；SQLite logical 欄位只有 hash、prefix 與 allowlist metadata；Codex state DB 無 aigo-inference cwd 的持久 thread，全域 config hash 不變 |

成本例：主模型 4,203 input、11 output，`4203 × 0.000002 + 11 × 0.00001 = 0.008516 USD`。小模型另有真實 cache hit：4,201 input（含 3,072 cached）、11 output，`1129 × 0.0000001 + 3072 × 0.00000001 + 11 × 0.0000005 = 0.00014912 USD`。兩筆均與回應及 LOG 相同。價格取自[公開 models 目錄](https://openrouter.ai/api/v1/models)，不是訂閱的額外扣款或 OpenRouter 實際帳單。

回歸：安裝 venv 的 `python -m pytest desktop_bridge/tests -q`：99 passed、2 Windows-only skipped；`node --test cloudflare/test/relay.test.js`：7 passed。`python tools/lint_terms.py --require` 已執行但失敗：沒有本機 `.banned-terms`／`BANNED_TERMS`。未以空清單或虛構清單繞過，仍是維護閘門的限制。

## 管理與限制

依 [source 安裝文件](CROSS-PLATFORM-INSTALL.md#macos-launchagent-管理與回復)，從 manifest 讀取目前 app，使用安裝內 `tools/mac_service.py status|start|stop|restart|rollback`。更新前 stop（內含 pause／wait-idle），在 checkout 重跑 `python3 tools/install.py`，重讀 manifest 後 start。rollback 保留 data；依賴不相容的大版本更新需同時恢復舊 requirements。不要重建空 profile、Worker 或 client key 來更新。

沒有重開電腦、沒有更改主機休眠設定；未實際讓整台 Mac 睡眠／喚醒或切換使用者訂閱，也沒有鎖住個人登入 Keychain。這些情況會離線或拒絕取用憑證，不能保證在休眠／未登入時服務。完全斷線且拿不到 usage 的未知 dispatch 不重做，也無法保證立即精確核帳。原生管理 UI／AI EA UI 未作本輪驗收閘門，不能寫成 UI 已通過。尚未發布 Mac release。

Cloud 注入與真實用量結算另有一組正式環境驗收紀錄；以該紀錄確認 Cloud 已完成，不能只用上述 Mac 43 項替代。
