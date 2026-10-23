# 資料字典與持久化邊界

實作來源：[store.py](../desktop_bridge/store.py)。本檔描述 logical schema，不包含任何安裝者資料或憑證。本次 UI 更新沒有 DB migration。

## SQLite

Mac source 另有 `macos-onboarding.json`：schema、installation_id、completed_at／completed_version、power_consent、key_id、verification（success、http_status、elapsed_ms、cost_usd、code、model、key_id、checked_at）。`macos-power.json` 存 schema、enabled、pending、original_sleep。兩者位於原 owner-only data-dir，沒有 KEY 或原始內容。`source-install.json` 新增 source_checkout，僅供明確來源更新；管理 session 只經 viewer stdin 傳遞。詳細生命週期見 [Mac 設定](MACOS-SETUP.md)。

profile 下 `bridge.sqlite`，WAL 模式、`secure_delete=ON`；並行存取用 RLock。版本目錄與 profile 分離。下列 nullable 依 SQLite 定義，不代表應用會為每筆提供值。沒有宣告 SQL foreign key；`requests.key_id` 是 API key 的邏輯關聯，拒絕請求可沒有 key。

### settings

| 欄位 | 型別／限制 | 意義 |
|---|---|---|
| name | TEXT PRIMARY KEY | 已知設定名稱 |
| value | TEXT NOT NULL | JSON 編碼值，不存 secret |

缺少設定回 `DEFAULTS`，不會一次寫入全部預設值。`device_id` 首次建立寫入隨機 UUID hex；不由硬體或訂閱帳號推算。

| 設定 name | JSON 型別／預設 | 更新與意義 |
|---|---|---|
| port | integer 8920 | 管理 UI 允許 1024–65535；重啟生效。隔離測試可由程式選動態 port。 |
| accepting | boolean true | 暫停／恢復接單；更新最低版本亦可限制新工作。 |
| retention_days | integer 30 | 1–365，只刪過期已結束 metadata。 |
| timeout_s | integer 180 | 10–1800；實際請求 deadline 可更短。 |
| inference_workers | integer 1 | runtime 驗 1–4；Windows 預設 1，Mac 由其獨立流程配置。 |
| public_url | string 空值 | HTTPS origin，不含 API path、query、fragment、帳密。 |
| default_model | string `openai/gpt-6-astra` | 省略／auto 使用此值；保留有效既有預設，失效優先找 Codex 再找第一筆。 |
| models | array DEFAULT_MODELS | 1–100 個唯一 id；每筆 `{id,provider,native}`，provider 為 claude／codex。 |
| claude_path | string 空值 | 空值自動偵測；不是登入憑證。 |
| codex_path | string 空值 | 同上。 |
| tunnel_kind | string none | 歷史相容設定；BYO 新安裝使用 Worker relay。 |
| tunnel_name | string 空值 | 選用既有 Named Tunnel；不代表自動部署。 |
| relay_enabled | boolean false | 需先有公開 URL 與配對 secret 才能啟用。 |
| device_id | string 首次 UUID hex | 安裝身分，登入切換不變。 |
| cloudflare_account_id | string 空值 | 首次 plan 綁定的自有 Cloudflare 帳戶。 |
| cloudflare_worker_name | string 空值 | 裝置 Worker 名稱，重複部署沿用。 |

startup 不在 settings 表，是 Windows HKCU Run／平台啟動設定；隔離 UI 測試不得誤改正式啟動設定。

### api_keys

| 欄位 | 型別／限制 | 意義 |
|---|---|---|
| id | TEXT PRIMARY KEY | 隨機 UUID hex |
| label | TEXT NOT NULL | 服務名稱，應用驗 1–60 字 |
| prefix | TEXT NOT NULL | 完整 KEY 的前 15 字元，供識別；不是可用 KEY |
| digest | TEXT NOT NULL UNIQUE | 完整 KEY 的 SHA256 hex；管理 API 不回傳 |
| created_ts | REAL NOT NULL | Unix 秒 |
| revoked_ts | REAL nullable | 非 null 表示撤銷 |
| providers | TEXT NOT NULL | JSON array；新 KEY 預設 claude／codex；無獨立模型白名單 |
| rpm | INTEGER NOT NULL | 每分鐘請求上限 1–600，預設 30 |

沒有 expires 欄位，KEY 長效直到撤銷／輪替。完整隨機 KEY 不寫 DB；建立／輪替一次回傳。輪替以同一交易建立新 KEY 並撤銷舊 KEY，保留 label／providers／rpm。

### requests

| 欄位 | 型別 | 意義／nullable |
|---|---|---|
| id | TEXT PRIMARY KEY | Bridge request UUID hex |
| key_id | TEXT | 邏輯關聯 api_keys.id；拒絕授權可為 null |
| model | TEXT | 已解析、已登錄外部 model id；前置拒絕可 null |
| provider | TEXT | claude／codex；前置拒絕可 null |
| created_ts | REAL | 建立 Unix 秒 |
| started_ts | REAL | 開始執行，尚未執行可 null |
| finished_ts | REAL | 結束，未結束可 null |
| status | TEXT | queued、running、completed、failed、rejected、cancelled、interrupted |
| http_status | INTEGER | 最終 HTTP code，尚未結束可 null |
| error_code | TEXT | 固定分類，不存原始 exception／stderr |
| duration_ms | INTEGER | 執行耗時，前置拒絕等可 null |
| input_bytes | INTEGER | 收到的 body bytes 數，不是 body |
| output_bytes | INTEGER | 模型回覆文字 UTF-8 bytes 數，不是回覆 |
| prompt_tokens | INTEGER | CLI 回報輸入；未知為 null |
| completion_tokens | INTEGER | CLI 回報輸出；未知為 null |
| cost_usd | REAL | OpenRouter 牌價估值；未知 null，不能把未知當零 |
| pricing_model | TEXT | 實際 CLI 模型對應的牌價 id |
| pricing_fetched_ts | REAL | 使用的牌價目錄取得時間 |
| cached_tokens | INTEGER | 可取得的輸入快取讀取 tokens |
| cache_write_tokens | INTEGER | 可取得的輸入快取寫入 tokens |
| reasoning_tokens | INTEGER | 輸出中的 reasoning 子集，不重複計費 |
| client_request_id | TEXT | 選用 UUID request 識別碼，用於去重／receipt；不納入一般 CSV |
| request_digest | TEXT | 帶 key id 的 canonical JSON SHA256，僅檢查識別碼內容衝突；不存原文、不納入 CSV |

所有非主鍵欄位在 SQL 層可 null，應用於各階段補入。索引 `requests_time(created_ts)`；`request_dedupe(key_id,client_request_id)` 是 client_request_id 非 null 時的 UNIQUE partial index。沒有原文／訊息／附件／完整 key 欄位。

`LOG_COLUMNS` 是一般寫入／更新／管理讀取／CSV 的 allowlist：上表除 client_request_id、request_digest 的 21 個欄位。只有專用 request_identity 路徑可寫入兩個內部去重欄位。管理匯出用 UTF-8 BOM，對 `= + - @` 開頭字串前置單引號避免 CSV formula injection。最多 10,000 列，UI 最多 500 列；clear 保留 queued／running。

## 非 SQLite 狀態

| 位置 | 內容／生命週期 |
|---|---|
| RAM tasks | 原始請求、結果、取消旗標及 rate window；結果最多約 10 分鐘，重啟不可恢復 |
| openrouter-pricing.json | 公開模型牌價、來源與 fetched_at；TTL 900 秒；沒有推論內容 |
| 配對 DPAPI 檔 | DEVICE_KEY，綁定目前 Windows 使用者；不是 client KEY；不入 repo 或安裝包 |
| windows-control.dpapi | 本次啟動的管理 owner 憑證；不在報告中輸出 token／fragment URL |
| windows-profile.json | 安裝根綁定既有 data-dir，避免更新改用另一 profile |
| windows-console.json | 自有 viewer pid、模式與版本；只用於該 profile 的生命週期 |
| updates/ | 已驗 policy、序號／狀態、pending 收據與 metadata／DPAPI 備份；不備份原始推論內容 |
| Cloudflare | 安裝者 Worker 設定／DEVICE_KEY secret；KEY digests 與請求結果 RAM 同步，沒有中央 Supabase |
| 供應商 CLI | 其原有登入區，Bridge 不複製 auth.json、不 logout/login、不改全域 config |

## 遷移、備份與刪除

啟動先 CREATE IF NOT EXISTS，再按 PRAGMA table_info 逐欄補上 cost／pricing、去重與 cache／reasoning 欄位。這是目前的 additive migration，尚無獨立 schema_version 表。未來不相容修改必須另訂遷移與最低可讀版本，不可假設任意舊版能讀。

啟動將 queued／running 設為 interrupted／503／process_restarted；原文不在磁碟，不能重播。更新使用 SQLite backup 並記 schema digest；recover 只允許原版本、相同 pack id／schema，不覆蓋新資料。手動備份不可只在運作時複製 sqlite 而漏 WAL；應停止此 profile 或使用 SQLite backup API。

刪紀錄不刪裝置身分或 KEY。撤銷不清理歷史計量。遺失完整 client KEY 需輪替；換 Windows 使用者／重灌即使保留 SQLite，仍須授權恢復 DPAPI／配對。見 [裝置生命週期](DEVICE-IDENTITY.md)。

## Windows onboarding 檔案（0.8.0 候選）

不新增 SQLite 表／settings 欄位；以下皆不保存原始 request／response 或完整 KEY：

| 檔案／位置 | 欄位與用途 |
|---|---|
| 安裝根 `windows-installation.json` | `schema=1`、`installation_id`；after-install 寫新 UUID，正常更新保留。不可與 device_id 混用。來源／舊包採 pack_id＋device_id 的穩定 fallback，新增安裝不刪原裝置資料。 |
| profile `windows-onboarding.json` | `schema=1`、`installation_id`、`completed_at`、`completed_version`、`power_consent`、`key_id`；新安裝 ID 清除流程完成狀態，不碰 SQLite。`verification` 僅 success、http_status、elapsed_ms（可缺）、cost_usd（可缺）、code、model、key_id、checked_at。 |
| profile `windows-power.json` | `schema=2`、`enabled`、`original_scheme`、`bridge_scheme`、`settings`（sleep／hibernate／unattended_sleep 支援項原 ac/dc）、`unsupported`。不保存或修改鎖定 HKCU。舊未發布 schema=1 已啟用設定需原候選先還原。 |
| profile `windows-power-elevation.json` | 短期 UAC 請求：schema、nonce、operation（apply/restore）、created_at；五分鐘失效、完成／取消清除。nonce 非 client KEY，helper 不執行任意命令、不更改任何 HKCU。 |

onboarding／power 使用 atomic replace，與 SQLite／DPAPI 同放原 profile 並納入更新備份。安裝 UUID 位於不被 current 版本替換的根目錄；更新不重產。完整 KEY、協作 handoff 含 KEY 版本、HTTPS回覆、一次完成 proof、Cloudflare 原始輸出及 OAuth token 不寫入上述檔案。帳戶 ID／Worker／URL 仍沿用 settings，CLI憑證仍由各 CLI 管理。

版本更新保留完成旗標，不會默默執行未同意的電源變更；既有無紀錄的安裝升級後需跑一次精靈。日後若有不相容 onboarding schema，要先定遷移與相對應驗收，不用「刪 profile 重來」處理。

## Mac runtime 互斥資源

0.8.1-mac.2 的全機單實例使用程序持有的 `127.0.0.1:8919` TCP bind；沒有 listener 或新持久化欄位／credential，DB schema 不變。profile 的 `instance.lock`／`activate.request` 繼續用於同 profile 管理視窗喚回。被拒絕的第二套不開啟 SQLite，不將另一套的 queued／running 誤標為 interrupted；僅可能建立 profile 鎖所需目錄／檔案。

## Mac 發布來源收據

source ZIP 的 `source-release.json` 只含 schema=1、format=macos-byo-source、version、40位 Git commit。無 .git 的下載安裝使用此收據核對 VERSION 並填入 source-install.json.source_commit。外部 macos-source-manifest.json 另含 target、dirty、redistributable、package、size、sha256、requires_python、architecture、signed、entrypoint；公開來源 metadata，不包含使用者／KEY／裝置憑證。
