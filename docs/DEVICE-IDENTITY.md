# 裝置、帳號與授權生命週期

`device_id` 是安裝者本機 Bridge 裝置設定檔的 UUID，保存在 SQLite；不是 Claude 帳號、Codex 帳號、email 或硬體指紋。固定 endpoint、client API key hash、模型設定與 metadata log 同屬這個設定檔。發布方沒有中央身分資料庫。

同一設定檔的 Claude／Codex 使用同一 Worker。供應商登入只決定某次推論可用的訂閱、模型與額度，不能重新配發裝置 URL／API key。新增或刪除模型也不更換裝置身分。

| 事件 | 需重新授權什麼 | endpoint／client key |
|---|---|---|
| Bridge 關閉、升級、電腦重啟 | 通常無；原資料須保留 | 不變。 |
| Claude／Codex 登入 token 過期／撤銷 | 該 CLI 由使用者重新登入；先 pause／wait-idle | 不變，未登入來源暫時回認證錯誤。 |
| 同 Windows 使用者切換 Claude／Codex 訂閱帳號 | 該供應商 CLI 的新帳號；不重配 Cloudflare | 不變，後續工作使用新登入的額度。 |
| Cloudflare CLI 的部署登入過期／切換操作者 | 部署時重新取得原綁定 account 的管理權限 | 不變；日常裝置 relay 不靠部署 OAuth。工具拒絕改到另一帳戶。 |
| 裝置 transport key 遺失／DPAPI 無法解密 | 原 Cloudflare owner 管理權限，repair-device-key | 保留原 DB／URL，僅 transport key 更新。 |
| 更換 Windows 使用者、刪除使用者 profile、重灌 | 授權恢復原 DB，原 Cloudflare owner 重配 DPAPI；新 OS 使用者自己登入供應商 | 恢復同一設定檔才可保留原 URL／key；全新空資料目錄會產生新裝置。 |
| 手動輪替／撤銷 client key | 本機管理者操作 | URL 不變；只有該 key 改變／失效。 |
| 刪除 Worker、改 account subdomain、真正搬 Cloudflare 帳戶 | 明確遷移與原／新 owner 權限 | workers.dev URL 不能保證不變；自有網域需保留並重新指向。client key 可在保留 DB 時不變。 |
| 新的實體電腦全新安裝 | 自己的 Cloudflare／供應商登入 | 預設新 UUID、新 Worker、新 key。 |

目前 Windows 預設資料在每使用者的 LOCALAPPDATA，配對憑證是 user-scope DPAPI。**不是任意 Windows 使用者登入同一硬體就自動共用的系統服務。** 若要保留原裝置身分，需經原擁有者授權搬移 DB 並重新配對；不會為了便利而把憑證放寬成全機所有使用者可解密。完整跨 Windows 使用者的常駐裝置 broker/service 尚未實作。

換訂閱前先暫停新工作並排空現有佇列；已開始的 CLI 可能持有舊帳戶 token，不能靠切換帳號保證正在執行的工作也改用新額度。Bridge 不自動關閉個人的互動 CLI。不必把 API key 改綁到新供應商帳號；若舊服務不應使用新額度，管理者明確撤銷／輪替該服務 key。

多個同供應商訂閱要同時運行，需真正隔離的 CLI credential profile／OS 使用者環境；單換 URL slug 無法做到。這版只跟隨其執行環境當前的 CLI 登入，不將多帳號自動切換列為已驗證能力。

備份只需裝置資料，不能把 request／response 保存作恢復依據。API key 只存 hash，備份不會還原明文 key；呼叫服務原先保存的 key 仍可在恢復同一 DB 後驗證。DPAPI 檔不可當成可跨帳號攜帶的明文密碼，也不提交／寄送給發布方。

參考：[Windows DPAPI 使用者範圍](https://learn.microsoft.com/en-us/windows/win32/api/dpapi/nf-dpapi-cryptprotectdata)、[Codex 登入與快取](https://learn.chatgpt.com/docs/auth)、[Claude Code 認證](https://code.claude.com/docs/en/authentication)。


## macOS source profile

macOS 使用原使用者登入 Keychain，配對項目的 account 由 data-dir 正規化路徑雜湊區分，active／pending 分開；不能將資料目錄任意搬家後聲稱 Keychain 自動跟隨。source 更新必須保留相同 data-dir。新 Mac 不使用 Windows DPAPI 檔；新建自己的 UUID、Worker 與 client key。Keychain 被鎖定／拒絕存取時停止配對或 relay，沒有明文替代；重新解鎖後 relay 採退避重連。失去原 Keychain 時需在原 Cloudflare 帳戶明確 repair-device-key，只改 transport credential；保留原 DB 才能沿用 client key hash。

LaunchAgent 屬於使用者 GUI 登入階段，並非未登入即可供應的系統 daemon。供應商登入、Cloudflare 部署 OAuth、Keychain 裝置 secret 與 client service key 是不同授權層；改訂閱不自動改 device_id、URL 或 client key。

## 同一台電腦的執行數量

產品契約是一台電腦只執行一個 Bridge runtime；Claude／Codex 共用這個設定檔與 Worker。Mac source 0.8.1-mac.2 起，不同設定檔、安裝目錄、本機 API port 或 OS 使用者都不能另開第二套；原 runtime 正常結束後才可切換設定檔。不複製原 DB／配對讓兩套連到同一 Worker。這個限制不刪除任何既有設定檔、Worker、URL 或 KEY，也不自動選另一套 profile 或切換 CLI 登入。Windows 待 [issue #20](https://github.com/AI-GO-APP/aigo-llm-bridge/issues/20) 修復；舊版不遵守新鎖，升級前先正常停止。
