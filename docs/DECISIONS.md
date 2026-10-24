# 產品決策紀錄

**D-30 採用 2026-10-23：Windows 全機 runtime 所有權。** 固定 Winsock exclusive reservation 在 DB／HTTP／relay 前取得，跨 profile／安裝路徑／API port／OS 使用者／TS session；同 profile event 只負責喚回視窗。忙碌 exit 3，controller 不重試；一般權限、無 UAC、無新增系統服務或管理憑證分享。LocalProbe 可測試隔離，正式不可切換鎖通道。跨使用者／session 僅在可拋棄 runner 以真 token／程序驗證，不動 owner 帳號；證據與限制見 [QA](qa/2026-10-23-windows-machine-runtime.md)。

**D-29 採用 2026-10-23：獨立產品識別。** 產品使用 Local Token Buffet Bridge，repo 改名為 `local-token-buffet-bridge`，UI／文件／專案描述移除歷史平台品牌與部署依賴說明。保留舊安裝的技術 namespace、profile、更新簽章與 immutable 資產，避免外觀改名改變裝置身分、URL 或 KEY；細節見 [BRANDING](BRANDING.md)。

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
| D-13 採用 2026-10-23 | **全面採合約請款系統視覺語言**：深藍側欄／表頭、靛藍主色、系統深淺色、token化卡片／表單，保留Bridge產品／功能。 | 維持獨立本機管理介面；提高小字對比及字級以符合本機管理用途。CSS變更需全頁及平台卡驗收。 |
| D-14 採用 2026-10-23 | **repo文件為可交接的產品體系**：需求、架構、schema、API、設計、決策、驗收互相連結；歷史產品明確標示；隨Windows包附上。 | 同PR同步更新受影響文件，CI只檢查覆蓋及連結，語意／實機證據仍須維護者判斷。 |

| D-15 採用 2026-10-23 | 純Markdown及指定QA圖片的文件收據不要求核心／Mac升版；避免每次補交付證據就產生無程式變更的新安裝包。 | CI排除範圍僅限文件／QA圖；runtime或偽裝為asset的程式仍須版本閘門。既有發布產物不可被文件更新替換。 |

## 如何變更決策

D-29（2026-10-23）：公開 API 的交付證據分為本機支援、無 Key 的路由可達性、明確推論驗證三層。401 僅證明路由已到認證閘門，不代表訂閱、成本或推論成功；health.online 只代表裝置連線。管理台 route evidence 五分鐘後標記過期，推論 metadata 附時間並僅在 RAM；CLI handoff 沒有外網證據時必須明示未驗。更新原 Worker 需使用者部署授權，不能因本機更新或路由檢查而自動部署。既有 Key／固定網址與裝置身分保留。

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
| D-26 採用 2026-10-23 | 0.9.0 整合 Jev Decisions 及模型發現，保留原 body／順序與 Windows 安全限制；每題實際模型／usage 核對後計價並聚合，不以未知量當免費。Windows 本機、更新及重啟驗收通過。 | 一般 LLM 的機率與 confidence 公式不代表 Jev 校準或原業務門檻準確；模型目錄不是 entitlement。公開新路徑目前 404，需 owner 另授權更新同一 Worker，本次不部署 Cloud，不發布 Mac package。 |


| ID／狀態 | 決定與理由 | 代價／何時重訪 |
|---|---|---|
| D-27 採用 2026-10-23 | **一台電腦只執行一個 Bridge runtime**，Claude／Codex 共用。Mac 0.9.1-mac.1 使用固定 loopback TCP bind 的 OS 原子所有權，跨 profile／API port／使用者，在 DB／relay 前拒絕第二套；同 profile 保留喚回管理台。 | 鎖地址被任何本機程式占用即拒絕；不自動切 profile、不終止原服務；舊版須先正常停止。只關管理視窗仍背景供應，停止須明確結束或排空 stop。Windows 實作及跨 session 原生驗收交由 issue #20，不用 Mac 證據代替。 |

| ID／狀態 | 決定與理由 | 代價／何時重訪 |
|---|---|---|
| D-28 採用 2026-10-23 | Mac 正式交付現行 BYO source ZIP 與專屬 macos-source-v… Release，Python 3.12+／WKWebView；以 tracked 公開檔 allowlist 建包，附 checksum／commit manifest／self-test，CI 從 ZIP 真安裝後發布。 | 不把 legacy desktop 包、Windows Velopack、未公證 .app／DMG 或更新 feed 混稱現有能力；Mac 日後升級沿用 profile、明確排空、下載新來源。發布後匿名回讀並驗 owner 更新及真 HTTPS。 |


**D-31 採用 2026-10-23：64 併發為標準。** 每裝置 Claude／Codex、Chat／Decisions 共用 64 同時推論；新 KEY 預設 600 RPM，保留既有頻率／裝置身分。串接採普通同步 API 並行 POST，無需工單或輪詢。控制請求另保留 8 名額，Schema 子程序保持 4 個並內部短暫等待。大於 64、Claude 真實負載及長上下文另列待驗。本次使用者明確授權更新既有裝置 Worker，並不將 Windows 發布變成對所有安裝者自動部署。

**D-32 採用 2026-10-23：Mac 64 容量沿用原地更新。** 新安裝使用共用標準；舊 profile 不隱式覆寫明確容量，由既有排空／停止／workers 指令設為 64。Mac Key handoff 預設 600 RPM，原 Key 頻率保留。本輪先跑少量公開 Chat／Decisions 與成本，另依新增授權本機 Claude 64 測試；不將 64 設定值視為負載實測。

**D-33 採用 2026-10-23：Mac 自行提高描述符上限。** LaunchAgent 繼承 256 軟上限，不足以容納 64 個 CLI 子程序與 socket。Bridge 啟動時只提高本程序 RLIMIT_NOFILE 軟上限至 4096（不超過硬上限），不改 launchctl、sysctl 或 LaunchAgent 以外設定。

**D-34 採用 2026-10-24：有界受理與可取消 FIFO。** #36 階段 0–1 補充 D-31：64 是驗證＋排隊＋執行的總受理數，執行預設仍為 64、可明確調低；舊明確 workers 缺 pending 者保留原受理容量。先保留名額再驗 schema，queued 取消／逾時／撤 Key 可移除及釋放，不等前方 CLI。同步受理時固定最長 90 秒，可被設定／外部 deadline 縮短；jobs 使用設定期限且含排隊。容量修改要求 paused＋idle，兩值原子更新；只存數值分段 metadata。不保證公開斷線即時取消，不自動重送未知結果。[門檻與代價](PERFORMANCE-PLAN.md)。

**D-35 採用 2026-10-24：Decisions 固定結構型別驗證。** #36 階段 2 只優化自有 noul/probabilities，不以「無 pattern」推斷外部 schema 安全；維持 bytes/depth／型別／有限值／範圍／機率語意。外部 schema 保留四個一次性隔離程序、3 秒及原平台預算，等待計入 request deadline。Mac 不宣稱有 Windows Job Object 等價 RSS hard limit。warm CLI 池移至 #39，須獨立驗證隔離與含補池的持續收益。

**D-36 採用 2026-10-24：合併重疊的唯讀登入狀態查詢。** 真訂閱 64 混合實測顯示 CLI auth status 的重複程序增加準備成本與 Chat p95。每個 Runtime 僅合併同 provider／auth generation、時間重疊的查詢；完成立即移除，不設 TTL、不保留憑證、不池化推論 CLI。等待者維持自己的取消／期限；查詢者取消時其他等待者可自行重新讀 metadata，絕不重送推論。generation 改變拒絕沿用結果。推論前 auth status 改用自有可取消程序群組，結束／回錯前清理；非推論的既有管理查詢契約保留。

**D-37 採用 2026-10-24：Claude 自有 Decisions 使用原生結構輸出。** 真訂閱發現僅提示 JSON 仍可能產生格式錯誤。只有 `DecisionSpec.inference` 可標記 generated_schema，Claude 使用已安裝 CLI 支援的 `--json-schema`，且要求 result 的 structured_output；原生結構終結步驟採 CLI --max-turns=2，同一題仍只啟動一次 CLI、沒有 Bridge 重送，tools 保持空集合；typed validator 仍獨立檢查數值與語意。argv 只含 repo 產生的固定 noul／probabilities 結構及陣列長度，不含 state／instructions／criteria 名稱／任意外部 schema；原始內容仍走 stdin／RAM。Chat 外部 schema 與 tools 不設此內部標記。Codex 原已有 stdin outputSchema，不改其協定。此能力不等於機率校準保證，不加重試。

**D-38 採用 2026-10-24：限制冷 CLI 啟動瞬間負載。** 同一 Runtime 僅對 Claude 自有 Decisions 使用最短 20 ms 的啟動間距，保持 64/64 受理／執行上限與既有 profile；不限制已啟動 CLI 的推論重疊數、不保留 warm CLI。64 筆 Decisions 同時到達的純間距最長約 1.26 秒，計入 provider_setup_ms 與既有期限。等待可取消／逾時，取消不留下未來預約名額；取得啟動機會後再核對 auth generation。一般 Chat 與 Codex 沿用原啟動方式；目的是降低移除 Decisions schema 子程序後，Claude 結構輸出集中冷啟動的 RSS／CPU 峰值，必須重驗原吞吐與 p95 門檻，不以名目容量當作實測通過。

**D-39 試驗 2026-10-24：單次使用 initialize-only warm CLI。** 先做獨立、預設關閉的 Codex 原型，一程序只供一題；不跨 Key／model／system 重用，不推論補池。Claude 須有經驗證的 ready 邊界才納入。常駐總數預設零並且不得大於 inference_workers，active＋warm＋refill＋closing 共用同一預算；後台控制項待固定效能／隔離／資源門檻通過才開放。root 上限不冒充 RSS／CPU 保證，未達門檻維持關閉，跨平台結果分開。詳見 [契約](WARM-CLI-PLAN.md)與 [Mac 試驗收據](qa/2026-10-24-macos-warm-cli-pilot.md)。


**D-40 Mac operator 試驗 2026-10-24：正式 API 可明確啟用 2/64。** owner 在 0.9.8 發布後要求實際常駐開關對照，故將 Codex initialize-only pool 接入 Runtime；新安裝維持零，不以小樣本取代 D-39 完整放行。兩 provider 推論 root 共用容量，Claude 無已驗 ready 邊界，維持 cold；不足名額時先清 idle，補池不超額。三設定由 paused／idle 專用 API 原子套用，管理台與 Mac CLI 同步，receipt 記真正 warm／cold 次數。分開記錄實作、owner 原機試驗與未通過的跨平台／尖峰門檻，後續外部測速可使用同一入口／原 Key。


**D-41 採用 2026-10-24：只在 Bridge 推論程序精簡 goals／技能。** issue 46 的短 Chat 約 4.2k 輸入主要包含 Codex harness；Mac 受控 loopback 已驗證 goals=false 與依 `skills/list` path 停用可移除對應宣告。每題使用同一 app-server 在 claim 前重新唯讀查詢，再以 thread/start typed dotted config 覆寫技能，避免第二程序、常駐舊清單與寫入個人設定；未知清單 fail closed，等待沿用原期限與取消。保留訂閱登入、每程序一題、ephemeral、無本機工具執行與完整計量。剩餘內建工具／權限／環境仍有固定成本；不更改管理員 requirements、不呼叫私有 provider endpoint、不跨 caller 重用 thread、不以未驗證旗標宣稱全部移除。後續若需純推論工具集合，另驗官方支援或上游變更；Decisions 合題另訂契約。Mac 實機與發布狀態見 [收據](qa/2026-10-24-macos-codex-context.md)，Windows 尚無此輪原生訂閱驗收。

**D-42 採用 2026-10-24：精簡內層工具宣告與原生格式化重複回合。** 依 issue 46／PR 49 的受控及真實單題測試，Codex 使用 `features.code_mode.enabled=false` 與 `excluded_tool_namespaces=["functions","clock"]`，取代 boolean code_mode，避免 TOML scalar/table 衝突；只覆寫 Bridge 子程序，不改管理員 requirements、登入或個人設定。外層 exec／wait／ask 工具宣告仍存在，執行禁止與事件拒絕仍獨立。Claude 只對 generated_schema 的自有 Decisions 在固定 system prompt 允許 StructuredOutput formatter 並要求直接呼叫；不是檔案／命令／caller tool 授權，仍 tools 空、strict MCP 空、restricted、單次 CLI、max-turns=2、typed validation 與完整 CLI usage。模型仍可能多步，不能保證每題一次模型回覆；不重送、不截短 caller 內容、不省略計量。僅驗 Codex 0.163.0-alpha.11／Claude 2.1.306；上游旗標仍開發中，新版本需重驗。Mac 發布與真 API 數據見 [0.9.11 驗收](qa/2026-10-24-macos-cli-token-release.md)，Windows 原生訂閱結果不由 Mac 推定。
