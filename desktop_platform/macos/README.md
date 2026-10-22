# Mac 安裝與維護

Python 3.10+；已在 macOS 以自己的帳號登入 Claude Code／Codex。安裝包不含 Python 或 CLI。

1. 解壓縮後雙擊 `Install.command`，或在解壓縮根目錄執行 `python3 desktop_platform/macos/install.py`。
2. 安裝程式登記找到的 CLI、保留既有 Bridge 金鑰，啟動個人端點並加入登入後啟動。
3. 金鑰：`python3 ~/.aigo-llm-bridge/desktop/aigo_desktop.py credentials`。

更新：解壓新版後重跑相同安裝指令。移除服務：相同指令加 `--uninstall`；設定與金鑰會保留。
只安裝不常駐：加 `--no-start`。可用 `--port 8792` 避開既有 Bridge。

服務：`~/Library/LaunchAgents/com.aigo.llm-bridge-desktop.plist`。
紀錄：`~/.aigo-llm-bridge/desktop/service.log`。安裝／解除安裝不需要 sudo。

本平台只依賴 `desktop/` 共用核心，不匯入 Windows 平台；建置入口 `python3 packaging/macos/build.py`。
完整說明見 [個人端點](https://github.com/AI-GO-APP/aigo-llm-bridge/blob/main/docs/13-desktop.md)。
