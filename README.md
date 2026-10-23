# LLM Bridge · Windows / BYO Cloudflare

在自己的 Windows 電腦使用既有 Claude Code／Codex CLI 訂閱，透過自己部署的 Cloudflare Worker，提供固定 HTTPS endpoint 與長效 API KEY。採 OpenRouter Chat Completions 相容子集、標準 POST／GET、只存中繼資料，並以 OpenRouter 公開牌價回傳數值型 `usage.cost`。

**不需要 AI GO 租戶或 Supabase，也不需要 OpenRouter KEY。** 發布方不代管安裝者的 Cloudflare、訂閱或入口。切換 CLI 訂閱不改裝置 URL／KEY。

## 安裝與交付

- **Windows 安裝器**：在 [GitHub Releases](https://github.com/AI-GO-APP/aigo-llm-bridge/releases) 選 `windows-installer-internal-v…`，執行其 Setup。此渠道使用 PyInstaller＋Velopack＋系統 Evergreen WebView2；尚無 Authenticode 公發憑證。詳細步驟見 [Windows 安裝與更新](docs/WINDOWS-INSTALL-UPDATE.md)。
- **首次 BYO 部署**：依 [BYO Quickstart](docs/BYO-QUICKSTART.md) 或把 [agent prompt](docs/AI-AGENT-SETUP.md) 交給自己的 AI agent。明確選擇自己的 Cloudflare 帳戶，CLI 引導不會擅自登入／登出供應商。
- **完成交付**：固定 endpoint、可用長效 client KEY、[第三方 AI IDE 串接訊息](docs/THIRD-PARTY-INTEGRATION.md)。完整 KEY 只顯示一次，放呼叫服務的 secret。
- **原始碼／Mac**：見 [跨平台安裝](docs/CROSS-PLATFORM-INSTALL.md)。Mac 安裝、驗收與 release 由其獨立維護者處理，Windows 通過不代表 Mac 通過。

## 產品規格與維護

[文件總入口](docs/README.md) 是完整交接起點，包含 [需求](docs/REQUIREMENTS.md)、[架構](docs/ARCHITECTURE.md)、[資料字典](docs/SCHEMA.md)、[API 相容矩陣](docs/API.md)、[視覺規範](docs/DESIGN-SYSTEM.md)、[決策](docs/DECISIONS.md) 及 [驗收](docs/ACCEPTANCE.md)。功能變更必須同步維護文件，不能只留在聊天或 LLM 記憶。

| 使用需求 | 文件 |
|---|---|
| 管理 KEY、LOG、模型與連線 | [管理台指南](docs/P1-Windows-guide.md) |
| 重啟、更新、換帳號、備份 | [裝置生命週期](docs/DEVICE-IDENTITY.md)、[Windows 更新](docs/WINDOWS-INSTALL-UPDATE.md) |
| 接入原 OpenRouter 服務 | [API](docs/API.md)、[第三方串接](docs/THIRD-PARTY-INTEGRATION.md) |
| token／成本與快取 | [牌價換算](docs/OPENROUTER-PRICING.md) |
| Cloud 呼叫端結算 | [整合最佳實踐](docs/AI-EA-CLOUD-BEST-PRACTICE.md) |

新 KEY 預設開放 Claude／Codex 全部已登錄模型，仍受訂閱及模型目錄限制；既有 KEY／輪替 scope 保留。每次可明確指定 model。不是 OpenRouter 全功能代理：streaming、抽樣控制、Responses 等未支援項目會明確拒絕；支援的 tools 僅產生提案，工具在呼叫端執行。

## 程式與 CI/CD

`desktop_bridge/` 是現行本機服務及共用前端；`cloudflare/` 是 BYO Worker 範本；`packaging/windows/` 是 Windows 薄殼、安裝與簽章更新。Windows 安裝器版本正本為 [release-target.json](packaging/windows/release-target.json)，與共用核心 `VERSION` 分離，不觸發 Mac release。

Windows 原生驗收使用 `Windows installer regression`；發布使用 `Windows installer package and publish`。GitHub 固定渠道 policy 配合 Ed25519 驗簽／最低版本檢查，支援通知及必要更新；不使用中央資料庫。原生 ZIP 為舊安裝路徑，不能與新版 Setup 混用同一程式目錄；資料沿原 profile 保留。

```powershell
python tools/check_product_docs.py
python -m pytest desktop_bridge/tests packaging/windows/tests -q
node --test cloudflare/test/relay.test.js
node --test packaging/windows/tests/platform.test.js
python tools/lint_terms.py --require
```

`hosted/`、`worker/`、`desktop/`、編號 01–13 文件與 [舊 README](README-LEGACY.md) 保留給歷史產品線，不作現行 BYO 契約。不能將其平台資料表、串流、短效 session 或雲端 fallback 描述套用到本產品。
