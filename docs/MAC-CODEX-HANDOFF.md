# Mac Codex 接手指引

此文件是可直接交給 Mac Codex 的工作指令。範圍為這台 Mac 的改造、安裝、BYO Cloudflare 部署與真實驗收；**先不要替換正式 Windows，也不要切換正式 Cloud 流量。**

## 一、程式來源與範圍

請接手 aigo-llm-bridge，在這台實體 Mac 完成相容性改造、本機安裝、BYO Cloudflare 部署與真實 Codex 訂閱呼叫驗收，最後交付可用的固定 HTTPS endpoint、長效 API KEY，以及第三方串接說明。請直接完成已授權工作，不要只提出計畫。

Repo：https://github.com/AI-GO-APP/aigo-llm-bridge.git

交接建立時已核對的功能基準為 main／來源標籤 v0.6.5：
`0354fbb9feb821f496db8ed5586c775db8446564`。

開始時重新核對遠端並讀取最新 main 的本文件。此 SHA 是功能基準，不是要求退回舊版。若 main 已更新，先檢查差異並記錄實際採用 commit；若已有 checkout、Mac 分支或未提交修改，先保留並檢查，不要 reset 或覆蓋。

目前 Windows 已有正式運行實例；macOS 尚待實機驗收。Windows release、既有 Mac 分支或 CI 成功，都不能當成這台 Mac 安裝成功的證明。

這是獨立的本機 Bridge，不是 AI GO 平台 Custom／Hosted App，不需要存取 AI GO 租戶。

本次可修改 Mac 相容程式、安裝與啟動流程、必要文件並部署這台 Mac 的專屬 Worker。不要修改 AI EA 應用、正式 Cloud provider registry、正式 Windows Worker、endpoint、KEY 或裝置資料。不要切換正式流量。

## 二、先讀專案規範

請先讀：

- [AGENTS.md](../AGENTS.md)
- [BYO skill](../skills/byo-cloudflare/SKILL.md)
- [跨平台安裝](CROSS-PLATFORM-INSTALL.md)
- [BYO 快速開始](BYO-QUICKSTART.md)
- [裝置與帳號生命週期](DEVICE-IDENTITY.md)
- [AI agent 安裝指引](AI-AGENT-SETUP.md)
- [AI EA Cloud 最佳實踐](AI-EA-CLOUD-BEST-PRACTICE.md)，尤其「下一階段：改用另一台 Mac 作常駐供應端」
- [第三方串接說明](THIRD-PARTY-INTEGRATION.md)
- [OpenRouter 成本換算](OPENROUTER-PRICING.md)

依文件使用 source 安裝流程；不要把 checkout 路徑當作實際安裝路徑。以安裝產生的 source-install.json 核對 app、Python runtime 與 data 路徑。

## 三、既有 Codex 訂閱與操作保護

預設使用這台 Mac 已安裝、已登入的 Codex CLI，透過現有 ChatGPT／Codex 訂閱進行推論，不改用 OpenAI API KEY。

先唯讀確認 CLI 版本、登入狀態與實際可用模型。不得自動 logout/login、切換帳號、改全域 ~/.codex 設定、MCP、hooks 或 auth.json，也不要操作使用者正在工作的 Claude Code／Codex 視窗。

若尚未登入或授權失效，請明確請使用者自行完成官方互動登入，再繼續；不要要求把 auth.json、OAuth token 或供應商憑證貼進聊天。

推論使用 Bridge 自己的隔離子程序與短暫 session。確認不在本機 CLI 介面留下持久對話，且不啟用不必要的主機工具。第三方送來的 tool call 是回傳提案，不代表允許在 Mac 執行 shell、MCP 或其他動作。

## 四、Mac 安裝與裝置生命週期

檢查並完成 Mac 實際需要的：

- 獨立安裝環境、依賴、啟動器與管理服務。
- Keychain 儲存及適當檔案權限；不得以明文儲存作為 Keychain 失敗的替代方案。
- LaunchAgent 登入後啟動、停止、pause／wait-idle、重啟及更新。
- 長效 KEY 建立、scope、輪替、撤銷與 LOG 管理。

不要搬用 Windows DPAPI 檔案。這台 Mac 建立自己的 device_id、設定檔、Worker 與 client KEY；不要和 Windows 共用運行中的裝置設定檔。

同一 Mac 設定檔重啟、更新、同帳戶重複部署後，URL 與仍有效的 KEY 必須不變。Codex／Claude 訂閱登入屬於另一層，不能因登入或切換訂閱自動重建 Worker、改 endpoint 或輪替 client KEY。

不需重開電腦。可在確認沒有進行中請求後，重啟本次 Bridge 程式來驗證。清楚說明 LaunchAgent 是登入後啟動，以及 Mac 休眠時無法持續供應推論的限制。

先完成本機實機驗收；不要把尚未驗收的 Mac 安裝包當正式 release 發布。所有修改保留為可審查的 Git commit。

## 五、BYO Cloudflare 部署

使用安裝者自己的 Cloudflare 帳戶與既有 CLI 登入。先以 whoami 等方式確認帳戶；有多個可能帳戶時，只詢問要使用哪一個，不猜測歷史實測帳戶或發布方帳戶。

透過 tools/byo_setup.py plan，明確指定 data-dir 與 account-id，產生這台裝置的部署設定，檢查後再依指南 deploy。不得直接部署 cloudflare/wrangler.jsonc 範本。

使用這台 Mac 專屬的具名 Worker，取得固定 workers.dev HTTPS 網址即可，不購買網域或方案。若首次 workers.dev 註冊或登入需互動，由使用者完成官方流程。

配對 secret、client API KEY、Cloudflare 部署授權與 Codex 訂閱憑證必須分離。不要將任何 secret 提交 Git、寫入報告或輸出到 CI。

## 六、真實驗收

不能只以單元測試、登入成功、localhost 或 HTTP 200 宣稱完成。使用合成內容，實際走：

HTTPS Worker → Mac Bridge → 已登入 Codex CLI → 真實模型回覆。

依既有支援範圍至少驗證：

1. GET /api/v1/models，以及實際可用模型。
2. 非串流 POST /api/v1/chat/completions，包含一般文字、多輪歷史與結構化 JSON。
3. 既有 tools／tool_choice 支援、131 tools 相容案例、tool result 接續；不執行提案中的真實主機動作。
4. 不支援的 OpenRouter 參數明確回 structured 400 unsupported_parameter，不靜默忽略或假稱等價支援。
5. usage 的實際 input／output／cache tokens，以及數值型 usage.cost。依實際模型對應 OpenRouter 公開牌價核算，驗證回應與 metadata LOG 一致；公開模型牌價查詢不需要另索取 OpenRouter API KEY。
6. usage.cost 是美元牌價等值，不是訂閱額外扣款。無法取得用量或價格時，不得捏造精確數值或用 0 掩蓋。
7. request ID、receipt、重複請求與錯誤恢復依現有契約運作；相同 generation 不重複推論或重複計費，未知 dispatch 狀態不得盲目重跑。
8. KEY 建立、輪替、撤銷、scope，以及 LOG 查詢／清理。
9. 程式重啟、更新、同帳戶重複部署後，使用原 endpoint 與原有效 KEY 再完成真實推論。
10. 斷線重連及相關失敗情境，清楚列出休眠與登入／Keychain 不可用的限制。

盡可能從另一台電腦或獨立外部 client 呼叫公開 HTTPS。若只有本機經公開網址測通，須明確標記「跨機來源待驗證」，不可冒稱已完成異地驗收。

原始 request、response、prompt 不落 Bridge 磁碟；LOG 僅保存 allowlist metadata。報告不包含原始內容、完整 KEY 或供應商登入資料。檢查安裝資料、暫存、例外與日誌，避免測試工具另行落下 payload。

執行 AGENTS.md 規定的回歸：

```sh
python -m pytest desktop_bridge/tests -q
node --test cloudflare/test/relay.test.js
python tools/lint_terms.py --require
```

使用實際安裝環境對應的 Python，另外完成必要的 Mac Keychain、LaunchAgent 與安裝更新驗證。管理功能本階段可用 API／CLI 驗收，不以原生畫面操作作為必要閘門；沒有測過的 UI 不標成通過。

## 七、Cloud 接手邊界

本次交付 Mac 候選入口，不替換正式 Windows。

後續由原 Windows／Cloud 接手端，在私有 AI-EA-Cloud 專案注入專用 secret，增加候選 provider，例如 bridge:mac-primary，並用 probe/mac-main、probe/mac-judge 測試別名做真實 Cloud 串接與核帳。

請提供：

- Cloud registry base_url：只有 HTTPS origin，不含 /api/v1。
- OpenRouter 相容 client base URL：<origin>/api/v1。
- Mac 實測可用的主模型、小模型 ID 與建議映射。

不要自行修改正式 Cloud registry、正常模型映射、既有 Windows secret 或 fallback。AI EA 的 Gate／業務判斷轉接留在 Cloud 層，Bridge 不加入 AI EA 專用問題或業務邏輯。

Mac 直接 HTTPS 驗收與完整 AI EA Cloud 串接／用量扣帳是兩道不同驗收；後者尚未執行時，清楚標記待接手。

## 八、完成交付

請交付：

- 實際 repo／分支／commit、Mac 改動摘要、macOS／架構／依賴與 Codex CLI 版本。
- 實際安裝、資料與啟動位置；啟動、停止、更新及回復方式。
- 固定 HTTPS origin、完整 API base URL、可用模型及標準 GET／POST 範例。
- 一把仍有效、供 Cloud 長期使用、scope 適當的專用 API KEY，以及非敏感 key ID／prefix。
- 依 docs/THIRD-PARTY-INTEGRATION.md 整理可複製給其他 AI IDE／Web IDE 的標準串接訊息。
- 每項真實驗收結果、失敗與限制，以及「Mac 已完成／Cloud 待接手」的明確狀態。

完整 KEY 透過本機管理介面一次性顯示或可信 secret 管道交付；不要放進 Git、一般報告或 CI。若缺乏安全交付管道，先讓擁有者在本機取得並安排交接，不要撤銷交付用 KEY 後宣稱完成。測試用 KEY 結束後撤銷，長期服務 KEY 保留有效。

請持續完成已授權的改造、安裝、部署與真實推論。只有缺少帳戶選擇、官方登入、Keychain 互動或需付費等必要條件時才詢問；不要為一般可逆步驟反覆要求確認。全程保留現有 Windows 正式服務。
