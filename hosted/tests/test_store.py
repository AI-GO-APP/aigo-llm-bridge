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
