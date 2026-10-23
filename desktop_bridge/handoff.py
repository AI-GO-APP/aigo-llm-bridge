"""A portable integration contract for another computer/IDE. No key readback."""
import json


def integration(store, model=None, providers=('claude','codex'), key=None, public_status=None):
    origin=store.get('public_url')
    if not origin:raise ValueError('請先完成自有 Cloudflare 部署。')
    models=[m for m in store.get('models') if m['provider'] in providers]
    selected=next((m for m in models if m['id']==model),None) if model else next((m for m in models if m['provider']=='codex'),models[0] if models else None)
    if not selected:raise ValueError('找不到此金鑰範圍可用的模型。')
    base=origin+'/api/v1'
    capabilities=origin+'/bridge/v1/model-capabilities'
    decisions_url=origin+'/api/alpha/decisions'
    decision_payload={'model':selected['id'],'state':'A synthetic customer asks for a quotation.',
                      'questions':{'needs_response':{'type':'noul','instructions':'Does the customer need a response?'}},
                      'provider':{'data_collection':'deny'}}
    payload={'model':selected['id'],'messages':[{'role':'user','content':'Reply exactly PONG.'}],'stream':False}
    config={'base_url':base,'api_key_env':'LLM_BRIDGE_KEY','model':selected['id'],
            'stream':False,'timeout_seconds':100,'max_retries':0,'max_concurrent_requests':64}
    credential=('LLM_BRIDGE_KEY='+key if key else 'LLM_BRIDGE_KEY 由擁有者另行提供；放入執行環境的 secret 設定。')
    status = public_status or {'state': 'unchecked', 'tests': []}
    status_text = {'needs_update': '公開 Worker 缺少新路徑：請先原地更新同一 Worker；Decisions／模型探索尚不可交付。',
                   'routes_reachable': '公開新路徑已可達認證閘門；仍需使用你的 key 完成真實推論驗收。',
                   'unreachable': '公開路由檢查未完成：請檢查網路、Worker 與裝置連線。'}.get(status.get('state'),
                   '公開 Worker 尚未檢查或證據已過期；以下是本機支援的路徑，不能當成外網已驗證。')
    evidence = [v for v in status.get('tests', []) if v.get('model') == selected['id']]
    evidence_text = json.dumps(evidence, ensure_ascii=False) if evidence else '尚無此模型的公開推論驗收紀錄。'
    prompt=f'''請將此專案的主要文字 LLM provider 接到我的裝置 Bridge，先檢查現有程式再修改設定與呼叫端。
公開狀態：{status_text}
Worker 版本：{status.get('worker_version') or '未知'}；路由檢查時間（Unix）：{status.get('checked_at') or '尚未檢查'}。
此模型的推論驗證 metadata：{evidence_text}（僅當次程序 RAM 紀錄；時間後續可能失效）。
Base URL: {base}
Models GET: {base}/models
Model capabilities GET: {capabilities}
Models refresh POST (body {{}}): {origin}/bridge/v1/models/refresh
Explicit model probe POST (消耗推論): {origin}/bridge/v1/models/probe
Chat POST: {base}/chat/completions
Jev Decisions POST: {decisions_url}
Authorization: Bearer $LLM_BRIDGE_KEY
Content-Type: application/json
{credential}
模型 ID: {selected['id']}
最小 request: {json.dumps(payload,ensure_ascii=False)}

標準容量為每裝置 64 筆同時推論，Claude／Codex 與 Chat／Decisions 共用總容量。請視為普通同步 API，以 async/await、Promise.all 或 HTTP connection pool 並行 POST，最多同時 64 筆。每筆直接取得結果，不需建立工單或輪詢；超過 64 尚未驗證。既有 key 的每分鐘上限仍依擁有者設定。
這是 OpenRouter 的部分相容介面。使用可自訂 base_url 的 OpenAI Chat Completions/HTTP adapter；不要預設選擇鎖定 openrouter.ai 的專用 adapter。
停用串流及自動工具呼叫。不要自動送 temperature、top_p、max_tokens、max_completion_tokens、tools、tool_choice、plugins 等預設值；不支援的非 null 參數會回 400 unsupported_parameter。0.6 起接受 provider.data_collection=deny/allow 作路由相容欄位，不影響接單，也不代表驗證訂閱資料政策。可另行啟用文字工具提案 tools/tool_choice，參數以 JSON Schema 驗證，工具由呼叫端執行；請先通過工具多輪驗收。需要串流的 IDE 仍不相容。
成功回傳 choices[0].message.content 及 usage；usage.cost 是依實際 token 與 OpenRouter 公開牌價換算的 USD 估值，不是實際扣款。不要使用 OpenRouter 帳務/key introspection、Responses API 或全模型目錄假設。
保留 TLS 憑證驗證。若 Python urllib 的 Windows CA store 尚未就緒，使用 certifi 的公開 CA bundle（或有效的 SSL_CERT_FILE），不可用 verify=false 繞過。
先 GET models，確認目標模型；再以最小 request 做真實 POST，檢查非空文字與數值型 usage.cost。只有真正通過才回報成功，不要只憑 HTTP 200 或程式設定判斷。
同時 GET model-capabilities，核對 availability.state、checked_at、expires_at。cli_catalog 是模型選單，不是每個模型都有訂閱權限的保證；unverified 需真實呼叫後才能驗證。refresh 不推論；probe 僅接受 model 與 protocol（chat 或 decisions），使用固定合成資料且會消耗訂閱用量。Claude 僅列登錄模型；不要為了查模型操作正在使用的 Claude 視窗或切換登入。
若專案原本呼叫 Jev，改接上面的完整 Decisions URL；只換 URL、Bridge key、model，保留 state、questions、criteria 與 provider.data_collection，其餘原有 Jev body 不要改成 messages。讀取 answers，不是 choices。最小 Decisions request: {json.dumps(decision_payload,ensure_ascii=False)}
Decisions 支援 noul、choice、score；noul 為機率，score 從 0 編號。這是以一般 LLM 模擬的答案，機率不等同 Jev 校準值；既有判斷門檻需重測。可建議選擇該 key 可見且驗證可用的 Luna 或 Haiku，明確指定模型後不自動替換。每題獨立推論，多題 input_tokens、output_tokens 與 usage.cost 都是實際呼叫加總，包含重讀 state 的成本。不要套用 Jev 或未執行的小模型牌價。詳見 docs/JEV-COMPATIBILITY.md。
Decisions 失敗可能已有消耗；以唯一 UUID 的 X-AIEA-Request-Id 查 /bridge/v1/receipts/<UUID>，核對 billing_status.complete 與已知累計成本。complete=false 不是免費；不要對 408 或斷線自動重送。
AI EA Cloud 整合另見 docs/AI-EA-CLOUD-BEST-PRACTICE.md；該 Cloud 直接以 usage.cost 作會員消耗，不需另一成本欄。
一般 POST 約 90 秒上限；客戶端 timeout 設 100 秒，自動重試設 0，408/斷線不自動重送以免重複推論。401 檢查 key（新建同步可能約 20 秒）；403 檢查來源 scope；429 檢查頻率/訂閱；503 檢查裝置在線、CLI 訂閱登入與牌價來源。
雲端/Web IDE 應從服務端呼叫並將 key 存入 server secret；不要放進瀏覽器 bundle 或公開 repo。此服務未提供瀏覽器跨域 CORS，不能直接由跨來源網頁前端呼叫。
裝置需保持開機、登入且 Bridge 運作；不必在這台呼叫端電腦安裝或登入 Claude/Codex。不要修改供應端的登入、Worker、URL 或輪替 key。'''
    return {'config':config,'request':payload,'prompt':prompt,'contains_key':bool(key),
            'model_capabilities_url':capabilities,'models_refresh_url':origin+'/bridge/v1/models/refresh',
            'models_probe_url':origin+'/bridge/v1/models/probe',
            'public_status': status,
            'decisions':{'url':decisions_url,'request':decision_payload,'response_path':'answers','mode':'emulated'}}
