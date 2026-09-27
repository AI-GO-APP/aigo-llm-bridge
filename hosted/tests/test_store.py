import asyncio
import json

import httpx
import pytest

from bridge.errors import BridgeError
from bridge.store import AigoStore


def make(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), headers={"Authorization": "Bearer t"})
    return AigoStore("http://platform.internal", "t", "biz_bridge_", client=client)


def test_request_shapes_and_field_mapping():
    seen = []

    def handler(req: httpx.Request):
        seen.append(req)
        if req.method == "POST":
            body = json.loads(req.content)
            return httpx.Response(201, json={"id": "row-1", "data": body["data"]})
        if req.method == "PATCH":
            return httpx.Response(200, json={"id": "row-1"})
        return httpx.Response(200, json={"items": [{"id": "row-1", "data": {"lookup_key": "k1", "owner": "u"}}],
                                         "total": 1, "page": 1, "page_size": 1})

    store = make(handler)

    async def go():
        row = await store.insert("jobs", {"key": "k1", "owner": "u"})
        assert row == {"key": "k1", "owner": "u", "id": "row-1"}
        await store.update("jobs", row, {"status": "done"})
        found = await store.find("jobs", [("key", "eq", "k1"), ("created_ts", "gte", 5)], sort="-key", limit=3)
        assert found == [{"key": "k1", "owner": "u", "id": "row-1"}]

    asyncio.run(go())
    post, patch, get = seen
    assert post.url.path == "/api/v1/open/data-center/tables/biz_bridge_jobs/records"
    assert json.loads(post.content) == {"data": {"lookup_key": "k1", "owner": "u"}}   # 一定要包 data
    assert patch.url.path.endswith("/records/row-1") and json.loads(patch.content) == {"data": {"status": "done"}}
    filters = json.loads(get.url.params["filters"])
    assert filters == [{"field": "lookup_key", "op": "eq", "value": "k1"},
                       {"field": "created_ts", "op": "gte", "value": 5}]
    assert get.url.params["sort"] == "-lookup_key" and get.url.params["page_size"] == "3"


@pytest.mark.parametrize("status,code", [(429, "store_rate_limited"), (403, "store_error"), (500, "store_error")])
def test_errors_become_503(status, code):
    store = make(lambda req: httpx.Response(status, json={"reason": "rule x"}))
    with pytest.raises(BridgeError) as e:
        asyncio.run(store.find("jobs", []))
    assert e.value.status == 503 and e.value.code == code


def test_platform_number_strings_are_coerced():
    """平台把 number 欄讀回成十進位字串;沒轉型時 `"0" > 0` 在綁定流程直接 TypeError(E2E 實踩)。"""
    def handler(req: httpx.Request):
        return httpx.Response(200, json={"items": [{"id": "r", "data": {
            "lookup_key": "k", "used_ts": "0", "expires_ts": "1790513946.3410000801086425781",
            "attempts": "2", "stream": False, "models": '["haiku"]', "owner": "12"}}]})

    rows = asyncio.run(make(handler).find("enrollments", [("key", "eq", "k")]))
    row = rows[0]
    assert row["used_ts"] == 0 and isinstance(row["used_ts"], int)
    assert abs(row["expires_ts"] - 1790513946.341) < 1e-3
    assert row["owner"] == "12"                      # text 欄不動,即使長得像數字
    jobs = asyncio.run(make(lambda r: httpx.Response(200, json={"items": [{"id": "j", "data": {
        "attempts": "2", "result_json": '{"a": 1}'}}]})).find("jobs", []))
    assert jobs[0]["attempts"] == 2 and jobs[0]["result_json"] == {"a": 1}
