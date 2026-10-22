"""A portable integration contract for another computer/IDE. No key readback."""
import json


def integration(store, model=None, providers=('claude','codex'), key=None):
    origin=store.get('public_url')
    if not origin:raise ValueError('請先完成自有 Cloudflare 部署。')
    models=[m for m in store.get('models') if m['provider'] in providers]
    selected=next((m for m in models if m['id']==model),None) if model else next((m for m in models if m['provider']=='codex'),models[0] if models else None)
    if not selected:raise ValueError('找不到此金鑰範圍可用的模型。')
    base=origin+'/api/v1'
    payload={'model':selected['id'],'messages':[{'role':'user','content':'Reply exactly PONG.'}],'stream':False}
    config={'base_url':base,'api_key_env':'LLM_BRIDGE_KEY','model':selected['id'],
            'stream':False,'timeout_seconds':100,'max_retries':0}
    credential=('LLM_BRIDGE_KEY='+key if key else 'LLM_BRIDGE_KEY 由擁有者另行提供；放入執行環境的 secret 設定。')
    prompt=f'''請將此專案的主要文字 LLM provider 接到我的裝置 Bridge，先檢查現有程式再修改設定與呼叫端。
Base URL: {base}
Models GET: {base}/models
Chat POST: {base}/chat/completions
Authorization: Bearer $LLM_BRIDGE_KEY
Content-Type: application/json
{credential}
模型 ID: {selected['id']}
最小 request: {json.dumps(payload,ensure_ascii=False)}

這是 OpenRouter 的部分相容介面。使用可自訂 base_url 的 OpenAI Chat Completions/HTTP adapter；不要預設選擇鎖定 openrouter.ai 的專用 adapter。
停用串流及自動工具呼叫。不要自動送 temperature、top_p、max_tokens、max_completion_tokens、tools、tool_choice、provider、plugins 等預設值；不支援的非 null 參數會回 400 unsupported_parameter，不會忽略。若 IDE 必須使用串流或工具才能工作，請明確回報不相容，不能宣稱已整合。
成功回傳 choices[0].message.content 及 usage；usage.cost 是依實際 token 與 OpenRouter 公開牌價換算的 USD 估值，不是實際扣款。不要使用 OpenRouter 帳務/key introspection、Responses API 或全模型目錄假設。
保留 TLS 憑證驗證。若 Python urllib 的 Windows CA store 尚未就緒，使用 certifi 的公開 CA bundle（或有效的 SSL_CERT_FILE），不可用 verify=false 繞過。
先 GET models，確認目標模型；再以最小 request 做真實 POST，檢查非空文字與數值型 usage.cost。只有真正通過才回報成功，不要只憑 HTTP 200 或程式設定判斷。
一般 POST 約 90 秒上限；客戶端 timeout 設 100 秒，自動重試設 0，408/斷線不自動重送以免重複推論。較長工作另接 /bridge/v1/jobs 的 POST + GET（此擴充不是 OpenRouter 規格）。401 檢查 key（新建同步可能約 20 秒）；403 檢查來源 scope；429 檢查頻率/訂閱；503 檢查裝置在線、CLI 訂閱登入與牌價來源。
雲端/Web IDE 應從服務端呼叫並將 key 存入 server secret；不要放進瀏覽器 bundle 或公開 repo。此服務未提供瀏覽器跨域 CORS，不能直接由跨來源網頁前端呼叫。
裝置需保持開機、登入且 Bridge 運作；不必在這台呼叫端電腦安裝或登入 Claude/Codex。不要修改供應端的登入、Worker、URL 或輪替 key。'''
    return {'config':config,'request':payload,'prompt':prompt,'contains_key':bool(key)}
