"""狀態存放:平台自建表(正式)或記憶體(開發、測試)。

為什麼時間一律存「epoch 秒」的 number 欄:平台的 datetime 欄不接受帶時區的值(結尾 Z 會 500),
讀回來又是不帶時區的 UTC;number 欄沒有這個坑,而且支援 gte / lte 過濾(租約、心跳要用)。

查詢限制(平台 records 平面):text 欄只有 eq / contains,number 欄才有 gte / lte;沒有 in、ne、OR。
所以每張表都有一個我們自己產生的 `key`(uuid)當查詢鍵,狀態一次查一個值。

查詢鍵在程式裡叫 `key`,存進平台表時叫 `lookup_key`(`key` 在部分 SQL 方言是保留字,
而實體名建立後永不可改,寧可一開始就避開)。對應只發生在 AigoStore 這一層。

表(邏輯名 → 實體名 = 前綴 + 邏輯名,預設前綴 biz_bridge_):
  jobs         local 工單與非同步呼叫
  workers      worker 名冊
  enrollments  一次性綁定碼
  usage        每次呼叫一列用量
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any, Protocol

import httpx

from .errors import BridgeError

Filter = tuple[str, str, Any]   # (欄位, eq|contains|gte|lte, 值)

SCHEMA: dict[str, dict[str, str]] = {
    "jobs": {
        "key": "text", "owner": "text", "source": "text", "provider": "text", "model": "text",
        "status": "text", "worker_key": "text", "session": "text", "request_json": "json",
        "partial_text": "text", "result_json": "json", "error_json": "json", "attempts": "number",
        "created_ts": "number", "lease_until_ts": "number", "done_ts": "number",
    },
    "workers": {
        "key": "text", "owner": "text", "key_hash": "text", "name": "text", "os": "text",
        "version": "text", "models": "json", "status": "text", "last_seen_ts": "number", "created_ts": "number",
    },
    "enrollments": {
        "key": "text", "code_hash": "text", "owner": "text", "source": "text",
        "expires_ts": "number", "used_ts": "number", "worker_key": "text",
    },
    "usage": {
        "key": "text", "source": "text", "owner": "text", "provider": "text", "model": "text",
        "served_by": "text", "status": "text", "http_status": "number", "stream": "boolean",
        "prompt_tokens": "number", "completion_tokens": "number", "cost_usd": "number",
        "duration_ms": "number", "created_ts": "number",
    },
    # 使用者自己選的優先順序(auto 路由用),一個 app × 使用者一筆
    "prefs": {
        "key": "text", "owner": "text", "source": "text", "priority": "text", "updated_ts": "number",
    },
}


def new_key() -> str:
    return uuid.uuid4().hex


def now() -> float:
    return round(time.time(), 3)


class Store(Protocol):
    async def insert(self, table: str, data: dict) -> dict: ...

    async def update(self, table: str, row: dict, patch: dict) -> dict: ...

    async def find(self, table: str, filters: list[Filter], *, sort: str | None = None,
                   limit: int = 50) -> list[dict]: ...

    async def by_key(self, table: str, key: str) -> dict | None: ...


def _match(row: dict, flt: Filter) -> bool:
    field, op, value = flt
    have = row.get(field)
    if op == "eq":
        return have == value
    if op == "contains":
        return value in str(have or "")
    if op == "gte":
        return have is not None and have >= value
    if op == "lte":
        return have is not None and have <= value
    raise ValueError(op)


class MemoryStore:
    """單一行程用。不適合 Hosted 正式環境(最多兩個實例、縮到零會清空)。"""

    def __init__(self):
        self.tables: dict[str, list[dict]] = {name: [] for name in SCHEMA}
        self._lock = asyncio.Lock()

    async def insert(self, table: str, data: dict) -> dict:
        async with self._lock:
            row = {**{f: None for f in SCHEMA[table]}, **data, "id": new_key()}
            self.tables[table].append(row)
            return dict(row)

    async def update(self, table: str, row: dict, patch: dict) -> dict:
        async with self._lock:
            for stored in self.tables[table]:
                if stored["id"] == row["id"]:
                    stored.update(patch)
                    return dict(stored)
        raise BridgeError(404, "not_found", "找不到這一列")

    async def find(self, table, filters, *, sort=None, limit=50):
        rows = [dict(r) for r in self.tables[table] if all(_match(r, f) for f in filters)]
        if sort:
            desc = sort.startswith("-")
            name = sort.lstrip("-")
            rows.sort(key=lambda r: (r.get(name) is None, r.get(name)), reverse=desc)
        return rows[:limit]

    async def by_key(self, table, key):
        rows = await self.find(table, [("key", "eq", key)], limit=1)
        return rows[0] if rows else None


class AigoStore:
    """平台自建表,經 Hosted App 容器的 Open Proxy(/api/v1/open/data-center/...)。

    整支 app 每分鐘 600 次的額度是共用的(不分端點、不分實例),呼叫端要自己節流。
    """

    def __init__(self, api_url: str, token: str, prefix: str, client: httpx.AsyncClient | None = None):
        if not api_url or not token:
            raise BridgeError(503, "store_not_configured", "容器內沒有 AIGO_PLATFORM_API_URL / AIGO_API_TOKEN")
        self.base = api_url.rstrip("/") + "/api/v1/open/data-center/tables"
        self.prefix = prefix
        self.client = client or httpx.AsyncClient(timeout=20.0, headers={"Authorization": f"Bearer {token}"})

    FIELD_MAP = {"key": "lookup_key"}          # 程式裡的名字 → 表上的實體名
    FIELD_UNMAP = {v: k for k, v in FIELD_MAP.items()}

    @classmethod
    def _out(cls, data: dict) -> dict:
        return {cls.FIELD_MAP.get(k, k): v for k, v in data.items()}

    def _url(self, table: str, suffix: str = "") -> str:
        return f"{self.base}/{self.prefix}{table}/records{suffix}"

    @staticmethod
    def _coerce(kind: str | None, value: Any) -> Any:
        """平台讀回來的 number 欄是十進位字串(例 "0"、"1790513946.341"),json 欄可能是字串。
        轉回程式要的型別;MemoryStore 的測試看不到這件事,所以放在讀取的唯一出口。"""
        if value is None or not isinstance(value, str):
            return value
        if kind == "number":
            if value == "":
                return None
            try:
                number = float(value)
            except ValueError:
                return value
            return int(number) if number.is_integer() and "." not in value.rstrip("0").rstrip(".") else number
        if kind == "boolean":
            return value.strip().lower() in ("1", "true", "yes")
        if kind == "json" and value[:1] in ("{", "["):
            try:
                return json.loads(value)
            except ValueError:
                return value
        return value

    @classmethod
    def _flat(cls, item: dict, table: str | None = None) -> dict:
        data = item.get("data") if isinstance(item.get("data"), dict) else None
        kinds = SCHEMA.get(table or "", {})
        row = {}
        for k, v in (data if data is not None else item).items():
            name = cls.FIELD_UNMAP.get(k, k)
            row[name] = cls._coerce(kinds.get(name), v)
        return {**row, "id": item.get("id")}

    async def _send(self, method: str, url: str, **kw) -> Any:
        try:
            resp = await self.client.request(method, url, **kw)
        except httpx.HTTPError:
            raise BridgeError(503, "store_unreachable", "平台資料表暫時連不上") from None
        if resp.status_code == 429:
            raise BridgeError(503, "store_rate_limited", "平台資料表額度已滿(每分鐘 600 次),請稍後再試",
                              headers={"Retry-After": resp.headers.get("retry-after", "5")})
        if resp.status_code >= 400:
            # 403 帶 reason / rule_id 代表租戶的資料存取規則擋下了 app 身分,改程式碼無解
            detail = ""
            try:
                body = resp.json()
                detail = str(body.get("reason") or body.get("detail") or "")[:200]
            except ValueError:
                pass
            raise BridgeError(503, "store_error", f"平台資料表回應 {resp.status_code} {detail}".strip(),
                              provider_status=resp.status_code)
        return resp.json() if resp.content else None

    async def insert(self, table: str, data: dict) -> dict:
        body = await self._send("POST", self._url(table), json={"data": self._out(data)})
        return self._flat(body, table) if isinstance(body, dict) else {**data, "id": None}

    async def update(self, table: str, row: dict, patch: dict) -> dict:
        await self._send("PATCH", self._url(table, f"/{row['id']}"), json={"data": self._out(patch)})
        return {**row, **patch}

    async def find(self, table, filters, *, sort=None, limit=50):
        params: dict[str, Any] = {"page": 1, "page_size": max(1, min(limit, 100))}
        if filters:
            params["filters"] = json.dumps([{"field": self.FIELD_MAP.get(f, f), "op": op, "value": v}
                                            for f, op, v in filters],
                                           ensure_ascii=False)
        if sort:
            desc, name = sort.startswith("-"), sort.lstrip("-")
            params["sort"] = ("-" if desc else "") + self.FIELD_MAP.get(name, name)
        body = await self._send("GET", self._url(table), params=params) or {}
        return [self._flat(item, table) for item in body.get("items") or []]

    async def by_key(self, table, key):
        rows = await self.find(table, [("key", "eq", key)], limit=1)
        return rows[0] if rows else None
