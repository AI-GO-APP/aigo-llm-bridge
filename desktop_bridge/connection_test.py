"""One synthetic inference through the configured client endpoint. RAM only."""
import json
import ssl
import time
import urllib.error
import urllib.request

import certifi


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a client credential to a redirected destination.


def probe(endpoint, model, key):
    started = time.monotonic()
    status = None
    success = False
    code, message = 'connection_failed', '無法連線，請確認網址、網路與 Bridge 是否在線。'
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    request = urllib.request.Request(endpoint + '/chat/completions',
        data=json.dumps({'model': model, 'messages': [{'role': 'user', 'content': 'Reply exactly PONG.'}], 'stream': False}).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json',
                 'User-Agent': 'aigo-llm-bridge-connection-test/1.0'})
    try:
        try: response = opener.open(request, timeout=60)
        except urllib.error.HTTPError as error: response = error
        with response:
            status = response.status
            if status == 200:
                raw = response.read(65537)
                try:
                    value = json.loads(raw) if len(raw) <= 65536 else {}
                    success = value['choices'][0]['message']['content'].strip() == 'PONG'
                except (ValueError, TypeError, KeyError, IndexError, AttributeError): pass
                code = 'ok' if success else 'unexpected_response'
                message = '已取得模型測試回應。' if success else '已連線，但未取得預期的模型測試回應。'
            else:
                code, message = {
                    401: ('unauthorized', '金鑰無效或尚未同步；新金鑰請稍後再試。'),
                    403: ('forbidden', '來源權限不足或入口拒絕請求，請檢查金鑰權限與入口設定。'),
                    429: ('rate_limited', '已達請求上限，請稍後再試。'),
                    503: ('unavailable', 'Bridge 暫停、離線或模型來源未就緒。'),
                    504: ('timeout', '等待模型回應逾時；工作可能仍在執行，請先查看請求紀錄。'),
                }.get(status, ('http_error', '入口或模型回傳錯誤，請查看請求紀錄。'))
                if 300 <= status < 400:
                    code, message = 'redirect_blocked', '入口要求重新導向，已停止傳送金鑰；請確認固定網址。'
    except (TimeoutError, urllib.error.URLError) as error:
        if isinstance(error, TimeoutError) or isinstance(getattr(error, 'reason', None), TimeoutError):
            code, message = 'timeout', '等待回應超過 60 秒；工作可能仍在執行，請先查看請求紀錄。'
    except (OSError, ValueError): pass
    return {'success': success, 'http_status': status, 'elapsed_ms': round((time.monotonic()-started)*1000),
            'code': code, 'message': message}
