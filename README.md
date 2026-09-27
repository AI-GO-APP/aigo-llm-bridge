# aigo-llm-bridge

> **English summary** — An OpenAI-compatible LLM gateway for AI GO Custom Apps and Hosted Apps.
> Callers change only a base URL and a key; the backend can be the Anthropic API, OpenRouter,
> or **the caller's own Claude Code running on the caller's own computer**. Status: early development.

讓 AI GO 上的 **Custom App** 與 **Hosted App** 用同一種 OpenAI 相容的方式呼叫 LLM,
後端可以切換:

| 後端 | `model` 寫法 | 誰付錢 | 適合 |
|---|---|---|---|
| Anthropic API | `anthropic/<model-id>` | 你的 API key,按量計費 | 正式環境的預設 |
| OpenRouter | `openrouter/<vendor>/<model>` | 你的 OpenRouter key | 已經在用 OpenRouter、要跨供應者 |
| 本人的 Claude Code | `local/self` | 呼叫者**本人**的 Claude 方案 | 呼叫者自己的工作、在自己的電腦上跑 |

**呼叫端只改兩個設定**(base URL 與 key),原本打 OpenRouter / OpenAI 的程式一行不動。

> ⚠️ `local/self` 有明確的使用邊界:**一個人的 Claude Code 只處理那個人自己送出的工作**,
> 不能替其他使用者運算、不能集中成一台共用機器。套件在伺服端強制這一條。
> 完整說明在 [docs/02-compliance.md](docs/02-compliance.md),啟用前請先讀。

## 架構一覽

```
Custom App 前端 ──(短效 token,SSE 串流)──────────┐
Custom App Server Action ──(HMAC / Bearer)──────┤
Hosted App ──(OpenAI 相容線路)──────────────────┤
                                                ▼
                              ┌─ Bridge(Hosted App,public + 自行驗章)─┐
                              │  /v1/chat/completions · /v1/responses   │
                              │  model 前綴路由 → anthropic / openrouter │
                              │                 → local:寫入工單佇列     │
                              │  狀態只存平台自建表(jobs / workers / usage)│
                              └────────────────────▲────────────────────┘
                                                   │ 主動輪詢(本機不需要對外開 port)
                              ┌─ Worker(使用者本人電腦)──┴──────────────┐
                              │  只認領「擁有者 = 自己」的工單             │
                              │  claude -p … --output-format stream-json │
                              │  逐段回傳 → Bridge 轉成 SSE 給等待的畫面  │
                              └──────────────────────────────────────────┘
```

每一條設計對應哪一道平台限制(Server Action 秒數上限、Hosted 單請求上限、實例數、縮到零、
本機沒有對外入口),寫在 [docs/01-architecture.md](docs/01-architecture.md)。

## 狀態與路線圖

目前版本見 [VERSION](VERSION),變更見 [CHANGELOG.md](CHANGELOG.md)。

| 階段 | 內容 | 狀態 |
|---|---|---|
| P0 | repo 骨架、術語、架構與合規文件、CI 禁字檢查 | ✅ |
| P1 | 實測四個關鍵數字(本機 CLI 延遲、瀏覽器直連串流、Server Action 同步上限、縮到零的輪詢命中) | 進行中 |
| P2 | Bridge v1:兩個相容端點、三種後端、工單佇列、驗章、用量帳 | 待 P1 |
| P3 | Worker v1:設備鑰匙、只領本人工單、串流轉發、心跳、開機常駐範本 | 待 P1 |
| P4 | 呼叫端套件:Custom App 區塊生成器、Hosted App helper、前端串流 hook | 待 P1 |
| P5 | 完整文件與 15 分鐘上手 | — |
| P6 | v0.1.0 發版(附端到端測試報告) | — |

## 目錄

```
docs/      設計、合規、部署、安裝、呼叫端、營運、API 參考
spikes/    P1 實測腳本(量完就把數字寫回 docs/01,腳本保留供重跑)
tools/     開發工具(禁字檢查等)
```

P2 之後會加入 `hosted/`(Bridge 服務)、`worker/`(本機 worker)、`clients/`(呼叫端套件)、
`examples/`(可直接發布的最小範例)。

## 參與開發

- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。
- **這是通用套件**:repo 內不得出現任何特定客戶、租戶、專案或人名。CI 的 `lint-terms` 會擋;
  範例一律用 `<your-tenant>`、`acme` 這類佔位。
- 提交前本機可跑:`python tools/lint_terms.py`(詳見該檔說明)。

## 授權

[MIT](LICENSE)
