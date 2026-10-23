# AI agent instructions

Windows 新安裝需依 [ONBOARDING](docs/ONBOARDING.md) 完成本人訂閱 CLI／Cloudflare OAuth、自有帳戶、一鍵或 AI IDE BYO、明確插電權限、真 HTTPS 與長效 KEY 交付；已完成者日常啟動不重跑。不得為驗收偷偷改 owner 工作站電源／鎖定，使用 fake adapter 或可拋棄 runner；UAC 只在本人明確點選後執行。CI/CD、release／policy 續期與失敗回復正本見 [CI-CD](docs/CI-CD.md)、[RELEASE](docs/RELEASE.md)。不依賴 AI EA Cloud／Supabase，不介入 Mac／其他 Cloud 專案。

先讀 [產品文件入口](docs/README.md)。需求、架構、資料字典、API、設計規範、決策與驗收都是 repo 正本；修改功能須在同一 PR 更新受影響文件。舊編號 01–13 及 README-LEGACY 僅供歷史產品線，不可套用到現行 BYO。新增取捨記 D 編號，不依賴聊天或 LLM 本機記憶。執行 `python tools/check_product_docs.py`；前端改動須依 DESIGN-SYSTEM 與 ACCEPTANCE 驗證六頁、深淺色、窄版及 Windows 適配卡。

0.4 起提供 repo 安裝器與第三方串接訊息：先讀 [安裝流程](docs/CROSS-PLATFORM-INSTALL.md)。Windows 原生 ZIP 與 source 安裝目錄分離。macOS 安裝、實機驗收與發布由獨立維護者處理，狀態見其驗收文件；Windows 工作不得發布 macOS release。首次安裝最終需交付 endpoint、一次性長效 key 及 [第三方 AI IDE 標準說明](docs/THIRD-PARTY-INTEGRATION.md)，不能只撤銷測試 key 後留下無法呼叫的安裝。

本專案目前是 Windows 本機 LLM Bridge，**只採 BYO Cloudflare**。每位安裝者在自己選定的 Cloudflare 帳戶部署、管理、付費及更新專屬 Worker；發布方只提供原始碼與安裝包，不代管入口、帳戶、裝置憑證或訂閱。這不是 AI GO 平台上的 Custom／Hosted App，安裝時不需存取 AI GO 租戶。

## 安裝或協助部署時

先讀 [BYO skill](skills/byo-cloudflare/SKILL.md)、[安裝指南](docs/BYO-QUICKSTART.md) 與 [裝置及帳號生命週期](docs/DEVICE-IDENTITY.md)。給使用者複製的 prompt 在 [AI-AGENT-SETUP](docs/AI-AGENT-SETUP.md)。

- 不要直接部署 repo 中的 `cloudflare/wrangler.jsonc` 範本。用 `tools/byo_setup.py plan --account-id ...` 產生每個裝置的本機專案；檢查明確的自有帳戶再 deploy。
- 不得將歷史實測報告中的網址、Cloudflare account ID 或配對資料當成新安裝的預設。新安裝沒有共享入口或預設 key。
- `device_id`、Worker 名稱、固定 endpoint、client API key 屬於裝置設定檔；Claude／Codex 登入是另一層。登入／登出／切換訂閱不得自動刪除裝置資料、重建 Worker 或輪替 client key。
- 同裝置設定檔的 Claude／Codex 共用一個 Worker；來源與模型用 scope 區分。不要按 provider 另建永久通道。
- 工具綁定 Cloudflare account ID。CLI 登入到其他帳戶時，應回原帳戶重新授權；不要為了讓部署成功而換 endpoint 或解除綁定。
- Windows DPAPI 綁定 OS 使用者。換 Windows 使用者時須經授權恢復原裝置資料、在原 Cloudflare 帳戶重新配對，不能聲稱會自動跨 Windows 使用者共用。
- 使用者自己的 CLI 已在使用時，不操作其視窗、不自動 logout/login、不改全域設定。要換訂閱，先 pause／wait-idle，由使用者完成登入，再檢查狀態並 resume。
- Cloudflare 部署登入、裝置配對 secret、外部 API key 與供應商登入憑證互相分離。不要要求將 Global API key、OAuth token、`auth.json` 或 DPAPI 檔貼進聊天／提交到 repo。
- 原始 request／response 不落磁碟，log 僅用 allowlist metadata。驗證使用合成內容，測試 key 結束撤銷；報告不含 token 或原始內容。

上述 repo 範本不單獨授權任何外部變更；依使用者本次安裝／部署要求在其選定帳戶操作。已取得明確部署授權及單一目標後，正常可逆步驟不需要反覆詢問。不要購買方案或網域，除非使用者要求。

## 維護

Windows 維護優先；macOS 依其獨立驗收文件，不把 Windows 結果當成 Mac 通過。保持外部標準 POST／GET 及明確 unsupported_parameter；不把非等價 CLI 控制宣稱為完整 OpenRouter 相容。改完執行 `python -m pytest desktop_bridge/tests -q`、`node --test cloudflare/test/relay.test.js`、`python tools/lint_terms.py --require`。BYO 建置見 `tools/build_byo.ps1`；不要將 `.desktop-data/`、`.desktop-build/`、`.wrangler/` 或任何安裝者設定打包／提交。
