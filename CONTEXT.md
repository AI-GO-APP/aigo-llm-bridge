# 現行產品術語

規格與維護入口：[docs/README](docs/README.md)。歷史 Hosted 詞義另存 [LEGACY-CONTEXT](docs/LEGACY-CONTEXT.md)，不可混用。

| 詞 | 現行意義 |
|---|---|
| Bridge | 安裝者電腦上的 desktop_bridge 本機服務；不是平台 Hosted App |
| Worker | 安裝者自己部署的 Cloudflare HTTPS 轉接服務；不是原歷史 Python worker |
| Relay | 本機出站長輪詢客戶端，RAM 轉送 Worker 工作 |
| Provider | claude／codex 本機 CLI 來源；不是 OpenRouter 自動路由 |
| model | 呼叫端指定、由本機目錄映射 native id 的模型 |
| auto | 保存的 default_model 別名，沒有 MoE 或付費 fallback |
| profile | 裝置的資料目錄：device_id、URL、KEY hash、metadata與受保護配對資料 |
| client KEY | 呼叫端長效 Bearer KEY，完整值只顯示一次；不是訂閱或管理憑證 |
| DEVICE_KEY | Worker 與本機 Relay 配對 secret，和 client KEY 分開 |
| 管理 token | 本機當次啟動的 management owner 憑證，外部 KEY 無管理權 |
| session | CLI個人對話不被Bridge接續；外部session_id僅驗證後丟棄 |
| job | Bridge非同步工作，內容／結果在RAM，SQLite只存metadata |
| receipt | KEY＋client request UUID 的執行／計費metadata，不是原文備份 |
| usage.cost | OpenRouter牌價USD等值，不是實際扣款或訂閱餘額 |
| core version | 共用VERSION；可能帶其他平台候選標記，不是Windows安裝器版本 |
| Windows version | packaging/windows/release-target.json；管理台優先顯示，獨立發布 |
