# Windows BYO 入口

Windows 新版請使用 [原生 ZIP 與 BYO 指引](../../docs/BYO-QUICKSTART.md)，或 [repo 安裝器](../../docs/CROSS-PLATFORM-INSTALL.md)。下方舊版個人端點僅供既有使用者維護，不含 Cloudflare 公開入口、長效 key 管理或成本換算。Windows release 已改用原生 BYO 包，與 macOS 分開發布。

# Windows 安裝與維護

Python 3.10+；已在 Windows 以自己的帳號登入 Claude Code／Codex。安裝包不含 Python 或 CLI。
CLI 必須是原生執行檔；不透過會重新解析文字的 `.cmd` wrapper。可用 `AIGO_DESKTOP_CLAUDE`／
`AIGO_DESKTOP_CODEX` 指向真正的執行檔。

1. 解壓縮後雙擊 `Install.cmd`，或執行 `py -3 desktop_platform\windows\install.py`。
2. 安裝程式登記找到的 CLI、保留既有 Bridge 金鑰，加入目前使用者的登入排程並啟動。
3. 金鑰：`py -3 "$env:USERPROFILE\.aigo-llm-bridge\desktop\aigo_desktop.py" credentials`（PowerShell）。

更新：解壓新版後重跑相同安裝指令。移除服務：相同指令加 `--uninstall`；設定與金鑰會保留。
只安裝不常駐：加 `--no-start`。可用 `--port 8792` 避開既有 Bridge。

排程名稱：`aigo-llm-bridge-desktop`。紀錄：`%USERPROFILE%\.aigo-llm-bridge\desktop\service.log`。
安裝目錄 ACL 限目前使用者；不需要系統管理員。

本平台只依賴 `desktop/` 共用核心，不匯入 macOS 平台；建置入口 `py -3 packaging/windows/build.py`。
完整說明見 [個人端點](https://github.com/AI-GO-APP/aigo-llm-bridge/blob/main/docs/13-desktop.md)。
