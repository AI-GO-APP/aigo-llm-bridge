# Mac 0.9.9：正式 API 常駐接入

owner 在 0.9.8 發布後明確要求 2 個常駐、64 執行／受理上限，對照短輸入 Chat 與 Decisions，完成後由外部使用者另做時間基準。這是 owner 選擇的 Mac operator 試驗；其他 profile 預設零。Claude 仍 cold，完整 64 burst／持續收益及跨平台放行繼續由 issue 39 追蹤。

Runtime 以 Codex initialize-only 建立可觀測 ready 的一次性資源；每題執行後關閉，兩 provider、待命、補池、closing 共用 root 容量。收據 execution 揭露實際 warm_hits／cold_starts。管理台新增獨立容量卡，paused＋idle 才能套用三值，0 關閉，禁止 bool／越界／常駐大於執行上限。

本機 Cocoa／WKWebView 六頁淺深色、1200／480 窄版、Mac 與 Windows 附加卡及新增容量卡已實際渲染，無水平溢出；接單中停用、非法 2>1 不寫設定、合法 0/64/64、暫停／恢復、剪貼簿、CSV Save／Cancel、KEY 清空與關 viewer 後服務均通過。證據在本機 `.desktop-build/099-console/`，不將 profile 或憑證打包。

公開發布、原安裝更新與實際 API 對照尚待本候選的 CI／Release 完成；不將本地假 CLI 測試當作真訂閱效能證據。
