# LLM Bridge · Windows / macOS · BYO Cloudflare

在自己的 Windows 或 Mac 電腦使用既有 Claude Code／Codex CLI 訂閱，透過自己部署的 Cloudflare Worker，提供固定 HTTPS endpoint 與長效 API KEY。Claude 與 Codex 在同一個 Bridge 設定檔共用一個 Worker／URL，呼叫時以 model 選來源。支援 OpenRouter Chat Completions 相容子集、標準 POST／GET、metadata-only 紀錄及數值 `usage.cost` 牌價估值。

不需要 AI GO 租戶、Supabase 或 OpenRouter KEY。Cloudflare 帳戶、訂閱與資料由安裝者擁有；發布方提供程式及安裝包，不代管入口。

## 先選作業系統與安裝方式

| 使用者／環境 | 安裝入口 | 首次啟動與日後更新 |
|---|---|---|
| Windows，一般使用者 | [Windows Releases](https://github.com/AI-GO-APP/aigo-llm-bridge/releases)：選 `windows-installer-internal-v…` 的 Setup.exe；[完整安裝指南](docs/WINDOWS-INSTALL-UPDATE.md) | 不需要 Python；Setup 後開 Bridge，依五步精靈完成。日後走應用內簽章更新。 |
| macOS，一般使用者 | [Mac 0.9.1-mac.1 source Release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases/tag/macos-source-v0.9.1-mac.1)：下載 ZIP 與 SHA256；[Mac 安裝／操作](docs/MACOS-SETUP.md) | 需要 Python 3.12+。解壓後執行 `Install.command`，再開安裝目錄的 `Bridge.command`，依五步精靈完成。日後下載新版，排空後更新同一安裝。 |
| AI Agent 協助安裝或原始碼安裝 | [可直接複製的 Agent prompt](docs/AI-AGENT-SETUP.md)、[雙平台 source 指令](docs/CROSS-PLATFORM-INSTALL.md) | 先辨識 OS、既有安裝與 data-dir；沿用安裝 manifest 的 Python／app／data_dir，不把 clone 當成永久服務。 |

[Windows 0.9.0 internal 已發布](https://github.com/AI-GO-APP/aigo-llm-bridge/releases/tag/windows-installer-internal-v0.9.0)，安全修補及 Jev／模型查詢已整合，正式 Windows 更新／重啟及成本驗收見 [0.9.0 收據](docs/qa/2026-10-23-windows-090-jev.md)。既有 Worker 不會隨 Windows 更新部署；新公開路徑仍需擁有者更新原 Worker。

Windows 使用 PyInstaller＋Velopack＋系統 WebView2；Mac 發布現行 BYO **source 安裝包**與 Cocoa／WKWebView 管理視窗，尚非已公證的 .app／DMG。Windows internal 包目前沒有 Authenticode 公發憑證。兩平台的版本、驗收與發布獨立；請依自己的平台選包，不使用歷史 `desktop-*` 安裝包。

## 首次安裝：人與 Agent 都依這條路徑

1. **準備依賴與訂閱**：安裝自己的 Claude Code 或 Codex CLI 並完成本人登入，至少一個來源可用。BYO 部署需 Node.js 24.22.1+（或 22.23.4+）、Wrangler 4.152.0 及自己的 Cloudflare OAuth；Mac source 另需 Python 3.12+ 與可用的登入 Keychain。已登入者沿用，不操作使用者正在工作的 CLI 視窗。
2. **安裝並開管理台**：依上表選包。Windows 新安裝優先 Setup；Mac 在解壓目錄執行 `python3 tools/install.py`（等同 Install.command），預設安裝在 `~/Library/Application Support/AIGO LLM Bridge`，然後開其中的 `Bridge.command`。
3. **完成五步精靈**：本人同意 AC 自動睡眠設定 → 檢查訂閱 CLI → Cloudflare OAuth／明確選自有帳戶 → 一鍵部署或交自己的 AI IDE 部署 → 建 KEY、真 HTTPS 測試與交付。電源設定不影響鎖定、螢幕、電池與實體按鍵；需要權限時由本人點選。
4. **保存交付**：完成後取得固定 endpoint、有效長效 client KEY 與[第三方串接訊息](docs/THIRD-PARTY-INTEGRATION.md)。完整 KEY 只在本機一次性介面顯示，存進呼叫端 secret；不貼進持久聊天、repo 或報告。
5. **確認可呼叫**：帶 Bearer KEY 的 models GET、合成 chat POST、預期回答與數值 usage.cost 均成功，才算交付。只有安裝、登入或 HTTP health 200 不代表完成。[BYO 細節](docs/BYO-QUICKSTART.md)、[Mac 五步說明](docs/MACOS-SETUP.md)、[Windows onboarding](docs/ONBOARDING.md)。

已完成者日常開啟不重跑安裝、OAuth 或部署。Windows 與 Mac 是兩台／兩個 OS 使用環境時，各用自己的設定檔與 Worker，不複製配對給同時在線的兩套服務；同一設定檔的 Claude／Codex 共用入口。

## 日常啟動、停止與更新

- **開啟／喚回**：使用已安裝的 Bridge 捷徑；Mac 使用 `Bridge.command`。Mac 一台電腦只允許一個 runtime，同設定檔重開只喚回視窗，另一設定檔被拒絕。Windows 全機限制另由 [issue #20](https://github.com/AI-GO-APP/aigo-llm-bridge/issues/20) 追蹤。
- **關視窗 X**：背景服務繼續供應。**結束 Bridge**：管理台明確確認後取消未完成工作並停止。Mac 若要先讓工作做完，使用 `mac_service.py stop`（pause／wait-idle 後停止）；`disable` 另停用登入自啟。詳見 [Mac 停止指令](docs/MACOS-SETUP.md)、[Windows 操作](docs/P1-Windows-guide.md)。
- **更新**：Windows 走管理台更新；Mac 依 [Release／來源更新](docs/MACOS-RELEASE.md) 先排空，再用新來源更新同一 install-root／data-dir。保留 device ID、Worker URL、KEY、模型、metadata 與登入；不因應用更新而重部署 Worker。舊 Mac runtime 須正常停止後才啟動新版本。
- **在線條件**：電腦未睡眠、網路與 CLI／Keychain 可用。停止後 Worker URL 仍存在，但不能由已停止的本機完成推論；休眠、登出、關機都會中斷供應。[裝置生命週期](docs/DEVICE-IDENTITY.md)。

模型能力查詢與 Jev Decisions 的 state／questions 串接見 [相容指南](docs/JEV-COMPATIBILITY.md)。新公開路徑需安裝者另授權更新原 Worker；本機應用更新不自動部署。

## API 與完整產品文件

[文件入口](docs/README.md) 包含[需求](docs/REQUIREMENTS.md)、[架構](docs/ARCHITECTURE.md)、[資料字典](docs/SCHEMA.md)、[API 矩陣](docs/API.md)、[設計](docs/DESIGN-SYSTEM.md)、[決策](docs/DECISIONS.md)與[驗收](docs/ACCEPTANCE.md)。新增功能與文件在同一 PR 維護，Agent 不依賴聊天記憶。

新 KEY 預設允許 Claude／Codex 全部已登錄模型，仍受來源 scope、模型目錄與訂閱限制；輪替既有 KEY 不擴權。每次可指定 model。主要 API 為非串流 Chat Completions；Responses、streaming、非等價抽樣等會明確拒絕，tools 僅產生由呼叫端執行的提案。[第三方串接](docs/THIRD-PARTY-INTEGRATION.md)、[牌價換算](docs/OPENROUTER-PRICING.md)、[Cloud 呼叫端整合](docs/AI-EA-CLOUD-BEST-PRACTICE.md)。

## 維護與發布

現行程式在 `desktop_bridge/`，BYO 範本在 `cloudflare/`；Windows [發布手冊](docs/RELEASE.md)與 Mac [發布手冊](docs/MACOS-RELEASE.md)分開，檢查依 [CI/CD](docs/CI-CD.md)。Windows Setup 不與舊原生 ZIP／source 安裝混用程式目錄。

```sh
python tools/check_product_docs.py
python -m pytest desktop_bridge/tests packaging/windows/tests tools/tests -q
node --test cloudflare/test/relay.test.js
node --test packaging/windows/tests/platform.test.js
python tools/lint_terms.py --require
```

`hosted/`、`worker/`、`desktop/`、編號 01–13 文件與 [舊 README](README-LEGACY.md) 是歷史產品線，不作現行 BYO 契約或安裝入口。
