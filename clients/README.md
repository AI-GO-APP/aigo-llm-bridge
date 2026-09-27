# clients:呼叫端的正本

三種呼叫環境各一份,都講同一套 API(docs/09)。複製進你的專案使用;不需要安裝套件。

| 檔案 | 給誰 | 怎麼用 |
|---|---|---|
| [`browser/bridge.ts`](browser/bridge.ts) | Custom App 前端 | 整檔複製到 `src/lib/bridge.ts`。需要一支 `bridge_session` action 換 token |
| [`custom-app/bridge_block.py`](custom-app/bridge_block.py) | Custom App Server Action | 「從這裡開始貼」到「到此為止」整段貼進每支 action(slug 必須是字面字串,所以不能 import) |
| [`python/aigo_bridge.py`](python/aigo_bridge.py) | Hosted App、任何伺服器程式 | 整檔複製;只用標準函式庫,Python 3.9+ |

三者都預設 `model: "auto"`,並把「使用者還沒選優先順序」回報成 `priority_required`,讓畫面先問使用者。
用法見 [docs/05](../docs/05-callers.md)、[docs/06](../docs/06-frontend-streaming.md)。

`examples/` 裡的副本由 `python tools/sync_clients.py` 從這裡同步;CI 以 `--check` 確認沒有飄移。
三者的行為測試在 `hosted/tests/test_clients.py`(對一個真的在跑的 Bridge 測)。
