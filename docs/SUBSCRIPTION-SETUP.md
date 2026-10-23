# 自備 AI 方案：買完或兌換後如何接上 Bridge

這份指南給剛購買或兌換 Claude／ChatGPT 方案的安裝者：確認方案可用、安裝官方 CLI、用**訂閱帳號**登入，最後讓 Bridge 認到。Bridge 只呼叫你自己電腦上已登入的官方 CLI，不保存、不經手你的密碼或 OAuth token。完成後再依 [Windows 首次設定](ONBOARDING.md) 或 [Mac 五步設定](MACOS-SETUP.md) 繼續 Cloudflare、KEY 與 HTTPS 測試。

指令與方案以官方文件為準：[Claude Code 安裝](https://code.claude.com/docs/en/setup)、[Codex 驗證](https://developers.openai.com/codex/auth/)、[Codex CLI](https://github.com/openai/codex)。本頁內容於 2026-10-24 對照官方文件整理。

## 1. 先確認方案與帳號

| 來源 | 可用方案 | Bridge 不接受 |
|---|---|---|
| Claude（Claude Code CLI） | Claude Pro、Max、Team、Enterprise | 免費 claude.ai 方案；Console／API key 登入（`ANTHROPIC_API_KEY`） |
| Codex（Codex CLI） | ChatGPT Plus、Pro、Business、Edu、Enterprise | API key 登入（`codex login --with-api-key`，依 API 牌價另計費） |

- **兌換碼／禮品卡**：先在官方網站（claude.ai 或 chatgpt.com）用要給 Bridge 使用的那個帳號完成兌換，確認帳號頁顯示方案已生效，再登入 CLI。CLI 登入的帳號必須就是有方案的帳號。
- **用量共用**：Bridge 的每筆推論都計入該帳號的方案額度，與你自己平常使用 Claude／ChatGPT 共用同一份額度。
- 只需要其中一個來源即可運作；兩個都接，呼叫端可依模型 ID 選擇。

## 2. 安裝官方 CLI

已安裝者跳過，只需確認版本能執行。安裝不需要系統管理員權限；不要用 `sudo npm install -g`。

**macOS**

```bash
# Claude Code（官方原生安裝，會自動更新）
curl -fsSL https://claude.ai/install.sh | bash

# Codex（擇一）
npm install -g @openai/codex
brew install --cask codex
```

**Windows（PowerShell）**

```powershell
# Claude Code（官方原生安裝）
irm https://claude.ai/install.ps1 | iex

# Codex（需 Node.js；PowerShell 擋 npm 腳本時改用 npm.cmd，不必降低 ExecutionPolicy）
npm install -g @openai/codex
```

其他方式：Claude Code 也可用 `brew install --cask claude-code`（macOS，需手動 `brew upgrade`）、`winget install Anthropic.ClaudeCode`（Windows）或 `npm install -g @anthropic-ai/claude-code`（需 Node.js 22+）。

安裝完**開新的終端機**，確認：

```bash
claude --version
codex --version
```

找不到指令通常是 PATH 尚未生效：開新終端機；Bridge 已在執行時，從管理台「結束 Bridge」後再開啟，讓 Bridge 取得新的 PATH。仍找不到時，可在精靈／管理台的進階區指定 CLI 的完整路徑。

## 3. 用訂閱帳號登入

登入一律由**本人**在瀏覽器完成授權。不要把密碼、驗證碼、OAuth token、`~/.codex/auth.json` 或 Keychain 內容貼給任何 AI、聊天室或發布者。

**Claude**

```bash
claude auth login
```

瀏覽器開啟後，用有 Pro／Max／Team／Enterprise 方案的 claude.ai 帳號登入並授權。若終端機詢問是否使用環境中的 API key，選否，否則會變成 API key 登入而不被 Bridge 接受。

**Codex**

```bash
codex login
```

選 **Sign in with ChatGPT**，不要選 API key。瀏覽器回呼受限（遠端桌面、無瀏覽器）時改用裝置碼登入：

```bash
codex login --device-auth
```

## 4. 確認登入方式正確

```bash
claude auth status
codex login status
```

| 指令 | Bridge 判定為就緒的條件 |
|---|---|
| `claude auth status` | JSON 中 `loggedIn` 為 `true`，且 `authMethod` 為 `claude.ai`；`subscriptionType` 會顯示方案 |
| `codex login status` | 指令成功，且顯示以 ChatGPT 登入 |

狀態正確只代表登入方式符合；模型權限與剩餘額度要以安裝精靈最後的真實 HTTPS 合成測試為準。

## 5. 讓 Bridge 認到

1. 開啟 Bridge 管理台或安裝精靈的「訂閱」步驟，按重新檢查。Codex／Claude 顯示就緒即完成。
2. 仍顯示未就緒：
   - 先結束並重開 Bridge（新安裝的 CLI 需要新的 PATH）。
   - 確認終端機的 `auth status`／`login status` 符合上表。
   - Mac：Claude 的登入存在使用者的登入 Keychain。請使用 0.9.4-mac.1 以上版本（保留 `USER` 環境，讓背景服務可讀取 Keychain 登入）。
   - 在進階區指定 CLI 完整路徑（`which claude`／`which codex`，Windows 用 `where.exe`）。
3. 接著完成 Cloudflare、KEY 與 HTTPS 測試：Windows 見 [ONBOARDING](ONBOARDING.md)，Mac 見 [MACOS-SETUP](MACOS-SETUP.md)。

登入、登出或切換方案不會改變此裝置的 URL、device ID 或 client KEY，不需要重新部署 Worker。

## 6. 換帳號、換方案或續約

1. 管理台暫停接單，等待進行中的工作完成（`byo_setup.py pause`、`wait-idle`）。
2. 本人在終端機執行 `claude auth login` 或 `codex logout` 後再 `codex login`，用新帳號登入。
3. 用第 4 節確認，再恢復接單（`resume`）。

完整流程與資料保留見 [裝置及帳號生命週期](DEVICE-IDENTITY.md)。只是續約或升級同一帳號的方案，不需要重新登入。

## 7. 常見問題

| 現象 | 原因與處理 |
|---|---|
| `authMethod` 不是 `claude.ai` | 用了 API key 或 Console 帳號。執行 `claude auth login` 改用訂閱帳號；移除終端機設定中的 `ANTHROPIC_API_KEY` 由本人判斷。 |
| Codex 顯示 API key 登入 | `codex logout` 後重新 `codex login`，選 Sign in with ChatGPT。 |
| 登入成功但推論回 429 | 方案額度或頻率限制已到，等待額度重置；與 Bridge 設定無關。 |
| 兌換後 CLI 仍顯示舊方案 | 確認兌換的帳號與 CLI 登入的帳號相同；必要時依第 6 節重新登入。 |
| 免費方案 | Claude 免費方案不含 Claude Code；請升級方案後再登入。 |

## 8. 給 AI 助手的安裝提示詞

以下提示詞可直接複製給 Claude Code、Codex、Cursor 等 AI IDE。AI 只負責安裝與檢查；**登入的瀏覽器授權必須由你本人完成**。

### 提示詞 A：安裝 CLI 並引導我登入

```text
我已購買／兌換自己的 AI 方案，要接上本機的 Local Token Buffet Bridge。請依 docs/SUBSCRIPTION-SETUP.md：
1. 判斷我的作業系統，檢查 claude 與 codex 是否已安裝（--version）。只安裝我要使用的來源：［Claude／Codex／兩者］。使用官方安裝指令，不用 sudo，不降低 PowerShell ExecutionPolicy。
2. 安裝後告訴我要在新終端機執行的登入指令（claude auth login／codex login），由我本人在瀏覽器完成授權。不要代我輸入密碼或驗證碼，不要要求我貼上 token、auth.json 或 Keychain 內容。
3. 我完成後，執行 claude auth status 與 codex login status，確認 Claude 是 authMethod=claude.ai、Codex 是 ChatGPT 登入；若是 API key 登入，請說明如何改用訂閱登入。
4. 不要 logout 我已登入的帳號、不要操作我開著的其他 CLI 視窗、不要改全域設定。
5. 最後提醒我在 Bridge 管理台按重新檢查；若 Bridge 在安裝 CLI 前就已啟動，先結束 Bridge 再開啟。回報每個來源的狀態，不要輸出任何憑證內容。
```

### 提示詞 B：只檢查目前登入狀態

```text
請只做檢查，不安裝、不登入、不登出：執行 claude auth status 與 codex login status，依 docs/SUBSCRIPTION-SETUP.md 第 4 節判斷 Bridge 能否使用各來源，列出原因與需要我本人完成的步驟。不要輸出 token、auth.json 或其他憑證內容。
```

### 提示詞 C：換帳號或換方案

```text
我要把 Bridge 使用的［Claude／Codex］換成另一個帳號。請依 docs/SUBSCRIPTION-SETUP.md 第 6 節與 docs/DEVICE-IDENTITY.md：
先暫停 Bridge 接單並等待進行中的工作完成，再告訴我要執行的登入指令，由我本人完成瀏覽器授權；我完成後檢查登入狀態，確認無誤再恢復接單。不要重新部署 Worker、不要更換 URL 或輪替 client KEY。
```
