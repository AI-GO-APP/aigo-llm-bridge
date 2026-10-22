# Windows 0.5.0 BYO 驗收

2026-10-22，在 Windows 11 執行。macOS 依使用者本輪指示標記待實機驗證，不發布 macOS。

## 新安裝者情境

實際執行 repo 安裝器到空白、隔離的安裝與資料目錄，使用安裝後的專用 Python／setup CLI／隨附範本完成自有 Cloudflare 部署，再由只持有生成契約與臨時 key 的獨立消費端程序呼叫公開 HTTPS。不是用假 provider 或 localhost 代替雲端路徑。

| 檢查 | 結果 |
|---|---|
| 空白設定檔 | 無預設入口或共享 key；安裝器建立專用 venv 與版本目錄 |
| 前置條件 | doctor 確認 Node／Wrangler 與現有 Codex 訂閱登入，不切換登入 |
| 自有 Cloudflare | 新裝置 Worker、DPAPI 配對成功，第一次交付前驗證真正的 HTTPS 裝置認證 |
| 一次性串接訊息 | 自有 base URL、Codex model、完整 key、非串流最小 request；之後的 handoff 無法讀回 key |
| 模擬遠端服務 | 獨立程序 GET models 200、POST chat 200、文字與唯一合成 marker 相符 |
| 成本 | 兩次真實回傳 usage.cost 皆為數值（0.08695／0.021326 USD）；cache 命中差異會影響金額 |
| 非等價控制 | temperature 明確回 400 unsupported_parameter |
| 更新／重部署／重啟 | 不同版本目錄，原 data_dir／UUID／Worker URL／同一 key hash 保持；同一 key 再次真實 POST 成功 |
| 撤銷 | 原 key 立即回 401；測試 key 均撤銷 |
| 內容不落地 | 7 個 profile 檔未含 key／合成 I/O；12 個變動 CLI 檔案的唯一 marker 命中 0 |
| 使用者環境 | 原生安裝 manifest、捷徑、啟動項不變；原有 40 個 Claude 程序皆保留；未操作視窗或登入 |

[安全中繼資料證據](windows-evidence/newcomer-0.5.0.json) 不含 key、原始 request／response、本機路徑或安裝者帳戶網址。

這是同一 Windows 上以獨立程序模擬其他電腦，網路確實經公開 Worker；不是另一實體電腦或真人新使用者的易用性測試。Cloudflare 使用已啟用 workers.dev 的自有帳戶；全新帳戶的官方註冊／選名互動仍由安裝者自行完成，文件已標明。不把 CLI whoami 成功、HTTP 200 或 source test 當成訂閱推論成功。

## 發布流程

Windows CI 針對 desktop_bridge 回歸、relay、原生 EXE／空白 profile／API key 認證及包內文件連結。packaging/windows/build.py 先核對根 VERSION 與執行版本，再產生原生 ZIP、SHA256 與來源 commit manifest。Desktop publish 選 windows 時，只建置及發布 Windows；macOS 工作不會被觸發。

既有 0.3.x BYO 安裝應使用同 InstallRoot 更新，保留資料及 key。舊 0.4 個人 loopback 端點與 BYO 是不同設定檔，沒有默默搬移其明文 key。原始碼流程見 [安裝指南](CROSS-PLATFORM-INSTALL.md)，第三方限制見 [串接指南](THIRD-PARTY-INTEGRATION.md)。

不能保證所有 IDE agent 都相容：需要可調整 Chat Completions base URL、停用 stream/tools。跨來源網頁需經自己的 server；CLI 更新、服務睡眠／喚醒、長時間負載仍需持續驗證。
