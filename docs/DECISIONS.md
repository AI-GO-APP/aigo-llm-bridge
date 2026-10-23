# 產品決策紀錄

此處是現行 BYO／Windows 決策正本。日期標示整理／確認日期，不捏造當初逐項決定的時間；先前取捨自使用者已採用方向與現行程式重建。新取捨須追加 D 編號，不靜默刪除歷史。

| ID／狀態 | 決定與理由 | 代價／何時重訪 |
|---|---|---|
| D-01 採用 | **BYO Cloudflare only**。每位安裝者自己的帳戶與專屬Worker；發布方不代管入口、帳單或憑證。 | 首次部署比共享服務繁瑣，需隨附agent prompt與CLI引導；若產品改成代管，先重訂責任及多租戶隔離。 |
| D-02 採用 | endpoint／KEY屬於裝置profile，與Claude／Codex account分開。兩來源同一Worker，用scope區分。 | 換OS使用者不能自動解DPAPI；需授權恢復／重新配對，不因CLI換帳號而重建URL。 |
| D-03 採用 | 主要介面為標準非串流POST／GET，OpenRouter相容子集；非等價欄位回明確400。 | 部分SDK預設參數需移除；只有能提供等價語意及真實I/O驗收才擴充。 |
| D-04 採用 | 不存原始request／response，只存allowlist metadata；回答與工作RAM化。 | 重啟不能還原回答／重播工作；metadata備份不代表對話備份；不能靠加debug原文排錯。 |
| D-05 採用 | usage.cost 用實際CLI模型的OpenRouter公開牌價等值；不需要OpenRouter KEY。 | 不是實際API扣款，缺有效價格在推論前拒絕；若需離線估值要另設明確過期政策，不能默默當0。 |
| D-06 採用 | **新KEY預設Claude／Codex全開**，允許來源中的所有已登錄模型；既有scope保留，輪替不擴權。 | 模型登錄／訂閱仍限制使用；未來每模型限制要另訂契約與遷移，不能回溯縮限新預設。 |
| D-07 採用 | 工具用結構化輸出adapter產生提案，執行由呼叫端處理。 | 不等同供應商原生完整tool calling；需驗原schema、歷史與用量，不開放本機工具。 |
| D-08 採用 | Windows用PyInstaller＋Velopack，版本／profile分離，CLI引導BYO。 | 無公發憑證時可能有OS警示；不得把Ed25519更新簽章描述成Authenticode。 |
| D-09 採用 | 系統Evergreen WebView2薄殼＋預設瀏覽器備援；共用前端與平台適配分開，不綁入整套Chrome。 | 依賴OS WebView2，需原生複製／儲存及缺少runtime備援；Mac殼由Mac維護者選擇並獨立驗證。 |
| D-10 採用 | GitHub immutable release＋固定公鑰policy、自建版本／最低版本比對，不使用中央Supabase。 | GitHub不可用時通知／更新可能延遲；反降版序號與本機已驗狀態保留，不以網路錯誤解除已知強制更新。 |
| D-11 採用 | Windows／Mac build、渠道及驗收獨立；Windows工作不發布Mac或部署安裝者Worker。 | 共用程式變更仍需測試兩方受影響範圍；Windows通過不算Mac驗收。 |
| D-12 採用 | Velopack明確HttpSource；排空後等自有viewer的OS程序真正退出再apply。 | 0.7.0／0.7.1需一次Setup／受控修復；不得只以視窗close事件判定更新安全。 |
| D-13 採用 2026-10-23 | **全面採合約請款系統視覺語言**：深藍側欄／表頭、靛藍主色、系統深淺色、token化卡片／表單，保留Bridge產品／功能。 | 並非搬入AI GO平台；提高小字對比及字級以符合本機管理用途。CSS變更需全頁及平台卡驗收。 |
| D-14 採用 2026-10-23 | **repo文件為可交接的產品體系**：需求、架構、schema、API、設計、決策、驗收互相連結；歷史產品明確標示；隨Windows包附上。 | 同PR同步更新受影響文件，CI只檢查覆蓋及連結，語意／實機證據仍須維護者判斷。 |

| D-15 採用 2026-10-23 | 純Markdown及指定QA圖片的文件收據不要求核心／Mac升版；避免每次補交付證據就產生無程式變更的新安裝包。 | CI排除範圍僅限文件／QA圖；runtime或偽裝為asset的程式仍須版本閘門。既有發布產物不可被文件更新替換。 |

## 如何變更決策

| ID／狀態 | 決定與理由 | 代價／何時重訪 |
|---|---|---|
| D-16 採用 2026-10-23 | Windows 每次全新安裝走可續接五步 onboarding，日常／正常更新保留完成狀態；安裝 UUID 與 device_id 分開。 | 重裝不抹 URL／KEY；0.7.x 無紀錄者需做一次；不可憑已有 endpoint 偽造電源同意。 |
| D-17 採用 2026-10-23 | 官方 CLI 授權＋自有 Cloudflare 明確選帳戶，一鍵 deploy 與 AI IDE prompt 兩路；不使用推論 CLI 當部署 agent。 | OAuth／新依賴仍由本人安裝核准；不自動改既有登入或遷移綁定帳戶。 |
| D-18 已被 D-21 取代 | 插電取消可控休眠／個人自動鎖定，先同意備份、保留 DC、讀回、可還原；權限不足可明確 UAC 窄 helper。 | 不覆寫企業安全政策、不禁止手動鎖定／強制關機；人體感測／廠商機制需本人檢查，不能宣稱取消全部硬體／組織鎖定。 |
| D-19 採用 2026-10-23 | 最終安裝以真 GET＋HTTPS POST／PONG／數值 cost／有效 KEY 交付放行；proof 只在 RAM。 | 重啟後未完成者需貼回保存的 KEY 重測，不默默用額度重試；fake／runner 不代表本人 OAuth／BYO 成功。 |
| D-20 採用 2026-10-23 | CI/CD／Release 拆為 repo 正本與隨包指南，參照 AI EA 的分層證據，但沿用 Bridge GitHub 靜態 signed policy。 | 不引入 Supabase／中央代管；Windows、Mac、安裝者 Worker 各自維護，發布收據明列未驗範圍。 |

| D-21 候選實作 2026-10-23 | 依使用者最新要求，縮小為 AC 三項自動睡眠／休眠設定，完全保留鎖定、螢幕、實體按鍵與 DC；移除鎖定檢查完成門檻、HKCU 寫入及常駐鎖定 guard。 | 正式發布前驗證真 Win+L 前／中／後 Codex I/O；一般權限優先，僅電源 ACL 不足時選用 UAC，不以鎖定政策要求提權。驗收狀態見鎖定 QA。 |

記錄觸發問題、選項、採用理由、資料／API／使用者影響及驗收。被取代項保留編號並指向新項。不要把「尚未實測」寫成「已決定不支援」，也不要從技術註解推論使用者批准了Cloud／帳號變更。

| ID／狀態 | 決定與理由 | 代價／何時重訪 |
|---|---|---|
| D-22 採用 2026-10-23 | Windows 0.8.1 安全修補：CA／runtime、Relay 拒絕 redirect、CLI 動態內容只走 stdin、Schema 子程序預算、Worker body 名額預留、依賴 hash／CVE 閘門。 | core 0.6.7 只標識共用修補，不發布 Mac；Worker 只交付範本，既有 Cloud 須擁有者另授權部署。沿用 URL／KEY／profile 與牌價換算。詳見 SECURITY。 |

| D-23 Mac source 候選 2026-10-23 | Mac 採獨立 Cocoa／WKWebView viewer，共用六頁前端與 BYO 驗證 coordinator；session 只走 stdin，關窗不停止 LaunchAgent。 | Mac UI／剪貼簿／CSV／生命週期獨立驗收，不把 Windows 結果當 Mac 證據。 |
| D-24 Mac source 候選 2026-10-23 | Mac 僅同意後改 AC idle sleep，先備份、讀回、可還原；來源更新使用已記錄 checkout 排空安裝、失敗回復。 | 保留鎖定、電池及個人登入；不借用 Windows 簽章 feed，不宣稱已有 Mac 公發更新渠道。 |
| D-25 採用 2026-10-23 | Windows 原生 0.8.2 在 entry 安裝獨占 loopback server adapter，阻止其他本機程序用 SO_REUSEADDR 重綁 API／管理埠。 | 不替換標準函式庫全域 class、不更動 source／Mac entry；占用時拒絕啟動而非接管。更新需真 Setup→A→B 與雙埠負面測試，不能靠常數存在判定修補。 |
