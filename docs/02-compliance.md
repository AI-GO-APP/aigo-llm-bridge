# 02 · 使用邊界(啟用 `local` 前必讀)

`local` provider 讓工作在「使用者本人電腦上的 Claude Code」執行。這一節說明它**能做什麼、不能做什麼**,
以及套件用哪些機制把邊界變成程式行為,而不只是文件上的約定。

## 1. 依據

Anthropic 的條款與 Claude Code 文件對訂閱方案(Pro / Max / Team / Enterprise)的登入憑證有明確限制,
重點是:

- 訂閱登入是給**個人在 Claude Code 與 Anthropic 自家 app 裡的一般使用**。
- 第三方開發者**不得**在自己的產品裡提供 claude.ai 登入或訂閱額度,包含以 Agent SDK 打造的產品;
  產品整合應使用 API key。
- 把訂閱憑證(包括 `claude setup-token` 產生的長效 token)拿到其他產品或服務裡使用,不在允許範圍內。

原文與最新版本以官方為準,啟用前請自行閱讀:

- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview)(文末關於登入與額度的說明)
- [Claude Code · Authentication](https://code.claude.com/docs/en/authentication)
- [Anthropic Consumer Terms](https://www.anthropic.com/legal/consumer-terms) 與
  [Commercial Terms](https://www.anthropic.com/legal/commercial-terms)

> 本文件是套件作者對條款的**保守解讀**與相應的技術設計,不是法律意見。
> 若你的組織需要以訂閱方案支撐產品功能,請直接向 Anthropic 取得書面同意,或改用 API key。

## 2. 套件允許的唯一形態

**一個人的 Claude Code,只處理那個人自己送出的工作。**

- worker 裝在使用者**本人**的電腦上,以使用者**本人**的 Claude 帳號登入(`claude` 互動登入)。
- 工單的 caller user 必須等於 worker 的 owner,Bridge 與 worker **兩端各檢查一次**。
- worker 呼叫的是 Claude Code 本體(`claude -p`),套件不讀取、不複製、不轉送任何 Claude 登入憑證。

## 3. 套件拒絕做的事

| 不做的事 | 為什麼 | 對應的程式行為 |
|---|---|---|
| 讓多位使用者共用一台 worker | 等同把一個人的方案額度提供給其他人 | 認領時比對 owner;不符就不發工單 |
| 找不到本人 worker 時改派給別人 | 同上,而且是靜默的 | 回 `409 no_worker_for_user`,由呼叫端決定改用 API 後端 |
| 在伺服器、容器或 CI 裡跑 worker | 那不是「本人的電腦」 | worker 啟動時要求互動登入狀態;不支援 `CLAUDE_CODE_OAUTH_TOKEN` 模式 |
| 讀取或搬運 Claude 憑證 | 憑證只屬於那台電腦上的 Claude Code | worker 只以子行程呼叫 `claude`,不接觸憑證檔 |
| 以 Claude Code 的名義對外呈現 | 品牌規範不允許 | 文件與介面用「本人的 Claude」,不用產品名當功能名 |

## 4. 仍然要由使用組織負責的部分

套件擋得住「技術上把工作交給別人的機器」,擋不住以下情況,請在導入時自行規範:

- 同一台電腦多人輪流登入不同帳號
- 使用者把自己的 worker 設備鑰匙交給他人
- 工作內容本身是否適合送到 Anthropic(資料分類、客戶合約)

## 5. 什麼時候不該用 `local`

- 需要無人值守、全天候的功能(使用者關機就停)
- 要替多個使用者、或替系統本身產生內容(例如排程報表)
- 需要可預期的吞吐量與 SLA

以上情況請用 `anthropic/*` 或 `openrouter/*`,呼叫端程式不必改,只換 `model`。
