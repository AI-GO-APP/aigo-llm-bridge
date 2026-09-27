# custom-app-client · S2 / S3 實測用的 Custom App

以 `starter-internal` 起手式建立,**只保留我們寫的檔案**;其餘(版面元件、`App.css`、`main.tsx`、
平台 SDK)沿用起手式原樣。起手式附的示範 action、示範頁與 `_template.json` 要刪掉
(`_template.json` 宣告了用不到的外部服務,不刪發布會被擋)。

| 檔案 | 作用 |
|---|---|
| `actions/spike_session.py` | 以 source 金鑰向 Bridge 換短效 token(綁 `ctx.user_id`) |
| `actions/spike_sync.py` | 同步呼叫 Bridge,伺服端延遲 N 毫秒,量 egress 截斷點 |
| `src/pages/SpikePage.tsx` | S2 直連串流 / 壞 token / 長連線,S3 延遲掃描 |

前置:外部服務 `llm-bridge-spike`(timeout_ms 30000)授權給這支 app;
secrets `SPIKE_KEY`、`BRIDGE_PUBLIC_URL`。
