"""呼叫端驗證:source 金鑰、HMAC 簽章、瀏覽器用的短效 session token;以及 worker 設備鑰匙。

session token 格式:base64url(JSON {"s": source, "u": user, "e": exp}) "." base64url(HMAC-SHA256)
只帶 source、使用者與到期時間,不帶任何權限;它能做的事由路由決定(只能打 /v1/*)。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

from .config import Settings
from .errors import BridgeError

HMAC_WINDOW_S = 300


@dataclass(frozen=True)
class Caller:
    source: str
    user: str          # 平台使用者 id;可能是空字串(系統身分,例如排程)
    kind: str          # key | hmac | session


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sig(secret: str, payload: str) -> str:
    return _b64(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())


def hash_secret(value: str) -> str:
    """設備鑰匙、綁定碼只存雜湊。"""
    return hashlib.sha256(value.encode()).hexdigest()


def new_secret(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def mint_session(settings: Settings, source: str, user: str, ttl: int) -> tuple[str, int]:
    exp = int(time.time()) + max(60, min(int(ttl), settings.session_ttl_max_s))
    payload = _b64(json.dumps({"s": source, "u": user, "e": exp}, separators=(",", ":")).encode())
    return f"{payload}.{_sig(settings.session_secret, 'session|' + payload)}", exp


def _verify_session(settings: Settings, token: str) -> Caller | None:
    parts = token.split(".")
    if len(parts) != 2 or not settings.session_secret:
        return None
    payload, sig = parts
    if not hmac.compare_digest(sig, _sig(settings.session_secret, "session|" + payload)):
        return None
    try:
        data = json.loads(_unb64(payload))
    except (ValueError, UnicodeDecodeError):
        return None
    if int(data.get("e", 0)) < time.time():
        raise BridgeError(401, "session_expired", "session token 已過期,請重新換發")
    if data.get("s") not in settings.source_keys:
        return None  # 發 token 的 source 已被移除
    return Caller(source=data["s"], user=str(data.get("u") or ""), kind="session")


def _source_for_key(settings: Settings, key: str) -> str | None:
    for source, expected in settings.source_keys.items():
        if hmac.compare_digest(key, expected):
            return source
    return None


def authenticate(settings: Settings, headers, body: bytes) -> Caller:
    """headers 用不分大小寫的對應(Starlette 的 Headers)。驗不過丟 401。"""
    if not settings.source_keys:
        raise BridgeError(503, "not_configured", "Bridge 尚未設定任何 source 金鑰(BRIDGE_KEY__<SOURCE>)")

    source_hdr = headers.get("x-bridge-source")
    if source_hdr:
        ts, sig = headers.get("x-bridge-timestamp", ""), headers.get("x-bridge-signature", "")
        key = settings.source_keys.get(source_hdr)
        try:
            skew = abs(time.time() - int(ts))
        except ValueError:
            skew = HMAC_WINDOW_S + 1
        if not key or skew > HMAC_WINDOW_S or not sig.startswith("sha256="):
            raise BridgeError(401, "bad_signature", "簽章無效或已過期")
        expected = hmac.new(key.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig[7:], expected):
            raise BridgeError(401, "bad_signature", "簽章無效或已過期")
        return Caller(source=source_hdr, user=headers.get("x-bridge-user", "").strip(), kind="hmac")

    raw = headers.get("authorization", "")
    token = raw[7:].strip() if raw.lower().startswith("bearer ") else ""
    if not token:
        raise BridgeError(401, "unauthorized", "缺少憑證")
    source = _source_for_key(settings, token)
    if source:
        return Caller(source=source, user=headers.get("x-bridge-user", "").strip(), kind="key")
    caller = _verify_session(settings, token)
    if caller:
        return caller
    raise BridgeError(401, "unauthorized", "憑證不正確")


def sign_request(key: str, source: str, body: bytes, ts: int | None = None) -> dict[str, str]:
    """呼叫端用的簽章 helper(也給測試用)。"""
    ts = int(time.time()) if ts is None else ts
    sig = hmac.new(key.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return {"X-Bridge-Source": source, "X-Bridge-Timestamp": str(ts), "X-Bridge-Signature": f"sha256={sig}"}
