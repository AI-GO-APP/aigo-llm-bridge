# Windows 管理台操作指南

檔名為歷史沿用；內容適用現行 WebView／BYO 管理台。完整規格入口：[產品文件](README.md)。本服務不需要外部租戶平台、Supabase 或 OpenRouter KEY。

## 安裝、首次部署與更新

Windows 新安裝使用 [Velopack Setup](WINDOWS-INSTALL-UPDATE.md)，不需要自行安裝 Python。程式版本與裝置資料分開，更新沿用同一 data-dir；不要把 source 安裝器、舊原生 ZIP 與 Setup 混用同一程式目錄。

Claude Code／Codex CLI 及訂閱由安裝者自己登入。Bridge 不 logout/login、不接續個人對話、不更動全域設定。部署自己的 Cloudflare 依 [BYO Quickstart](BYO-QUICKSTART.md) 或執行包內 CLI `aigo-bridge.exe setup`；account 必須明確屬於安裝者，勿直接部署 repo 的 wrangler 範本。

同一裝置 profile 保留 device_id、Worker URL、KEY及metadata。CLI切換訂閱不變URL／KEY；換Windows使用者／重灌不保證DPAPI可解，見[裝置生命週期](DEVICE-IDENTITY.md)。首次交付要有可用KEY與[標準串接訊息](THIRD-PARTY-INTEGRATION.md)，不能只給網址。

## 開啟與關閉

捷徑開啟系統WebView2薄殼；缺少runtime或主動選備援可用預設瀏覽器。兩者使用相同管理頁與本機管理token。管理台只監聽127.0.0.1，不把client KEY當管理憑證。

按X／關閉分頁只關管理畫面，背景繼續接單；要停止整個服務，在設定或側欄選「結束Bridge」並確認。登入後自動啟動可在設定管理，不是Windows系統服務。重啟後從捷徑取得新的管理連線；不可把本機動態管理URL當第三方固定endpoint。

## 六個頁面

| 頁面 | 操作與注意事項 |
|---|---|
| 總覽 | 分別看有效KEY、工作數、CLI唯讀登入狀態與轉接連線；已設定公開URL不等於Worker在線。可暫停／恢復接單。 |
| 串接指南 | 複製Base URL、選模型與呼叫範例。測試連線需主動輸入KEY並送出，會各呼叫Claude／Codex而使用額度；輸入送出後清空，不保存KEY。 |
| API金鑰 | 建立1–60字服務名稱與1–600RPM。新KEY預設兩來源全開，無每模型白名單；仍需登錄模型及訂閱可用。完整KEY只顯示一次，可複製KEY或含KEY的IDE訊息。輪替保留scope／RPM，舊KEY立即失效；撤銷／輪替取消其未完成工作。 |
| 請求紀錄 | 篩選狀態／來源，查看耗時、token、牌價估值USD與固定錯誤分類。最多顯示500筆；CSV最多10,000筆，UTF-8 BOM。清除確認會刪所有已結束紀錄，包括目前篩選以外項目；執行中／排隊保留。 |
| 模型管理 | 編輯外部id→來源→native id。每次請求可指定model；省略／auto用已保存預設。保存清單保留有效既有預設，移除預設時優先Codex再第一筆。模型登錄不代表訂閱有權限或牌價可查。 |
| 連線與設定 | 儲存公開HTTPS origin、配對DEVICE_KEY後啟用relay；管理port、保存天數、timeout、CLI路徑及自動啟動。Windows包另有CLI引導、版本／渠道、更新操作。 |

## 串接與成本

使用標準 `POST /api/v1/chat/completions`、`GET /api/v1/models`，Bearer長效KEY。長工作用Bridge jobs端點。完整[API相容矩陣](API.md)列明必填／選填／null／unsupported規則；不能把OpenRouter SDK預設附加的temperature、max_tokens或stream:true直接送入。

tools／tool_choice／工具歷史是經schema驗證的提案adapter，工具在呼叫端執行，不會啟用本機shell或MCP。一般模式Claude單turn、Codex可多輪；不是完整OpenRouter或Responses支援。

usage.cost以CLI回報token和實際模型的OpenRouter公開牌價計算，為USD等值估算，不是訂閱扣款／餘額。未知cost顯示破折號，不當零；價格不可用在推論前失敗。參見[成本規範](OPENROUTER-PRICING.md)。

## 隱私、故障與恢復

只持久化[資料字典](SCHEMA.md)中的設定、KEY hash與metadata。原始訊息、附件、回覆、完整KEY、任意metadata與CLI stderr不寫磁碟；RAM結果會過期，重啟不會回放原請求。不是OS pagefile／crash dump或供應商雲端的零留存保證。

關機後固定Worker網址仍存在，推論會離線；恢復同profile即可沿用。未知執行結果先查receipt，勿無限自動重試。遺失完整KEY只能輪替。Windows更新通知／必要更新來自GitHub簽章policy；不需Supabase，詳見[安裝與更新](WINDOWS-INSTALL-UPDATE.md)。


標準容量為每裝置 64 筆同時推論，Claude／Codex 與 Chat／Decisions 共用。請以普通同步 API 並行 POST（async/await、Promise.all 或連線池），每筆直接取得結果；串接不需工單或輪詢。新 key 預設 600 RPM，既有 key 頻率另行核對。超過 64 尚待驗證，詳見 [併發規格](CONCURRENCY.md)。
