"""統一的錯誤形狀:{"error": {"code", "message", "provider_status"}}。"""

from __future__ import annotations


class BridgeError(Exception):
    def __init__(self, status: int, code: str, message: str, provider_status: int | None = None,
                 headers: dict[str, str] | None = None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.provider_status = provider_status
        self.headers = headers or {}

    def body(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "provider_status": self.provider_status}}

    def response(self):
        from fastapi.responses import JSONResponse   # 延後載入:工具程式只用錯誤型別,不需要 web 相依
        return JSONResponse(self.body(), status_code=self.status, headers=self.headers)


def provider_error(provider: str, status: int | None, message: str = "", retry_after: str | None = None) -> BridgeError:
    """把上游狀態碼翻成 Bridge 的錯誤。

    上游 401/403 代表 **Bridge 的** 供應者金鑰有問題,不是呼叫端的,所以回 502 而不是原樣回 401 ——
    否則呼叫端會以為自己的 source 金鑰錯了。
    只有 400 類附上游訊息(前 300 字):那通常是請求形狀的問題,開發者需要看到;其餘一律不回原文。
    """
    if status is None:
        return BridgeError(502, "provider_unreachable", f"{provider} 暫時連不上")
    if status in (400, 422):
        return BridgeError(400, "provider_bad_request", (message or f"{provider} 拒絕了這個請求")[:300], status)
    if status == 404:
        return BridgeError(400, "model_not_found", f"{provider} 找不到這個模型,或帳號沒有權限使用", status)
    if status == 413:
        return BridgeError(413, "request_too_large", "請求太大", status)
    if status == 429:
        headers = {"Retry-After": retry_after} if retry_after else {}
        return BridgeError(429, "provider_rate_limited", f"{provider} 限流中,請稍後再試", status, headers)
    if status in (401, 403):
        return BridgeError(502, "provider_auth", f"Bridge 的 {provider} 金鑰無效或權限不足,請聯絡管理者", status)
    if status == 402:
        return BridgeError(502, "provider_billing", f"Bridge 的 {provider} 帳戶有計費問題,請聯絡管理者", status)
    return BridgeError(502, "provider_error", f"{provider} 暫時無法服務", status)
