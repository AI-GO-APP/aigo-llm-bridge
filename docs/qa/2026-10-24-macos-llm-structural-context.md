# Mac 一般 LLM 結構性上下文研究

日期 2026-10-24；Refs #46；計畫／契約見 [LLM-CONTEXT-PLAN](../LLM-CONTEXT-PLAN.md)，metadata 見 [證據](../concurrency-evidence/macos-llm-structural-context-2026-10-24.md)。

**候選研究完成，未整合 runtime／未發布。** 正式仍是 0.9.11-mac.1，source `f9b481047485a9be8c0351a3b44139064e021c86`，原 profile／Key／URL／常駐 2／workers 64／pending 64。依 owner 最新指示，Decisions 的 StructuredOutput 保持原樣；本輪亦未採用前輪 Decisions schema-dedup／thinking-off 候選。

後續D-44已於0.9.12發布並更新原安裝，見 [新收據](2026-10-24-macos-chat-minimal-release.md)。本頁保留研究當時的候選狀態，不代表目前正式版仍未整合。

## 原生 CLI 真實用量

直接啟動獨立的已登入訂閱 CLI，每次一程序一題、全程串行、零 Bridge 推論重送。模型為 gpt-6.1-sol／claude-haiku-4-5-20251001；CLI Codex 0.163.0-alpha.11、Claude 2.1.306。不是公開 Bridge receipt、不是正式 pool 效能基準。

| 模型／固定案例 | caller 估算 | 現行 input → 候選 | output | 秒數現行 → 候選 |
|---|---:|---:|---:|---:|
| Codex／短題，caller-only | 5 | 2,634 → 11 | 6 → 6 | 4.2372 → 3.6090 |
| Codex／500 文字，caller-only | 500 | 3,127 → 506 | 6 → 6 | 3.8583 → 3.7786 |
| Claude／短題 | 5 | 565 → 527 | 70 → 47 | 1.7519 → 1.4555 |
| Claude／500 文字 | 500 | 1,061 → 1,022 | 104 → 77 | 1.9602 → 1.7963 |

500 是同份 caller 文字的 `o200k_base` 估算；**沒有真 OpenRouter receipt，也不是 Claude tokenizer**。input/output 為 CLI 原生完整 usage。Codex 500 文字 input 減少 83.82%，與 caller 估算差 6（1.2%）；output 同為 6，候選 total 512。Claude 對同份文字 input 減少 3.68%，仍有明顯固定開銷；不要把其估算差直接當成 provider 精確 overhead。

Codex 分兩段：先移除 agent 工具／context，保留 Bridge 固定 base/developer prompt，短題 52 input／6 output、4.5095 秒，500 文字 547／6、3.8434 秒；再用 caller-only，移除 Bridge 固定前綴及固定 developer 提示，caller system／developer／歷史不變，得到上表 11／506。後段不是刪 caller instructions，也沒有移除實際 sandbox／never approval／工具清單與事件拒絕。caller-only mock 的 provider instructions 欄位未出現、caller block 完整且 tools／additional_tools 空；不要把「空 prompt」解讀為繞過執行限制。

Codex 另驗歷史訊息 71 input／18 output（reasoning 10）、不可信工具指令 79／6、initialize-only 等待後單次領取 547／6、caller JSON schema 80／15；模型、格式與語意簡檢全通過。initialize／initialized 後等待 0.5 秒，領取前 thread/start=turn/start=skills/list=0，領取後各一，結束程序清理。這一筆證明 ready 邊界，不代表多 profile 正式池已完成。caller schema 是普通 Chat，不是 Decisions。

caller-only 另驗不可信工具指令 42 input／6 output、歷史 30／20（reasoning 12），語意簡檢通過，所有 caller 訊息仍送出。system／歷史的訊息邊界有不同 overhead，不能將單一 user 題的差 6 外推到每種請求。

16 次真 CLI 合計 **10,901 input／405 output**；其中 Codex 12 次 7,726／107、Claude 4 次 3,175／298。全部 cache read=0，Claude cache write=0；沒有 Bridge 推論重送或失敗刪樣，原生輸出完整計量。Codex 兩段 history reasoning 分別為 10／12，其餘均 0；Claude 未提供同型 reasoning 拆帳，不臆填零。Claude output 可能含推理，不能只用答案字數估 usage。單題時間受模型／網路波動，第一段 Codex 短題還略慢，本輪沒有延遲改善或費用比例保證。

## credential-free mock 與根因

共 12 次 loopback：Codex 拆解 5 次、thread-only 覆寫 1 次、500 caller 完整性 2 次、caller-only 1 次，Claude 拆解 3 次，零真模型推論。HOME／CLI config／XDG 為拋棄目錄；Codex provider requires_openai_auth=false 且無 Authorization header，Claude 僅明確 fake API KEY 送 loopback，不讀／轉送 owner auth。只存欄位型別、工具名稱、布林、長度、token 估算與 hash，不存 raw body／headers／event／stderr。

Codex wire input JSON 的 o200k 估算（**不是計費**）：

| 覆寫 | JSON input 估算 | additional_tools 估算／狀態 |
|---|---:|---|
| 現行 | 3,159 | 2,426，外層工具仍在 |
| 只關 request-user-input | 2,584 | 1,844，exec／wait 仍在 |
| 只關環境／權限／協作等注入 | 2,655 | 2,426，工具仍在 |
| direct catalog＋關 request-user-input | 699 | 無 additional_tools，環境仍在 |
| direct＋關上述 context | 190 | tools 空、additional_tools 空 |

僅 thread/start config 放入候選設定，仍有 1,844 的 additional_tools，因為 model manager 使用 app-server **啟動**時的 catalog。必須設計 profile 相符的資源租用，不能直接用現有 generic pool 冒充候選。

500 文字在兩 arm 的模型輸入各只有一個 caller block，2,497 UTF-8 bytes、估算 500、相同 SHA256 `42d278f79ca7749939bc2648c9ef2cb44a28087355a42ec5b58800197cc7efc3`。候選 tools／additional_tools 均空，沒有靠截短 caller 減量。所有 mock 完成且 session／child 關閉、無 rollout／Claude session jsonl。

Claude 現行 system／messages JSON 估算 118／380，minimal text 96／366，native message 96／365，皆 tools 空；三者仍有四段 system-reminder，包括環境／cwd／平台及模型知識資訊。改輸入格式只差約一個 JSON token，沒有繼續做沒有成效的真訂閱重測。

## 來源與覆寫邊界

對應 Codex 上游 tag `rust-v0.163.0-alpha.11`，source commit `5425d3e625daa58eea3ad1de27c087eb3b2ffbd3`。只讀公開來源，沒有編譯、fork 或修改 owner CLI。

- [tools/mod.rs](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/core/src/tools/mod.rs#L63)：模型 tool_mode 優先於 feature flags。
- [模型目錄](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/models-manager/models.json)：選定項目為 code_mode_only。候選僅改 tool_mode=direct、shell_type=disabled、apply_patch_tool_type=null、experimental_supported_tools=[]，不改模型 ID、權限或 transport。
- [config_toml.rs](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/config/src/config_toml.rs)：include_permissions_instructions／include_apps_instructions／include_collaboration_mode_instructions／include_environment_context／include_environment_context_time；這些在本版 source 存在，但未在下方公用 config reference 列出，僅本版原生驗證，不宣稱穩定跨版本 API。
- [thread_manager.rs](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/core/src/thread_manager.rs#L449)、[message_processor.rs](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/app-server/src/message_processor.rs#L340)：model manager 的啟動 catalog 邊界。

官方 [Codex config reference](https://learn.chatgpt.com/docs/config-file/config-reference) 明列 model_catalog_json 啟動載入；[Open Source](https://learn.chatgpt.com/docs/open-source) 指向公開 CLI／app-server repo。本輪使用子程序 argv 的固定設定與公開 metadata 檔，caller 內容仍 stdin／RAM，保留原生 auth、實際隔離及事件拒絕，不抽取 OAuth 或使用 private provider endpoint。

Claude [CLI reference](https://code.claude.com/docs/en/cli-reference) 的 --system-prompt／--tools 已用於 mock／真實驗證；[環境變數](https://code.claude.com/docs/en/env-vars) 說明 SIMPLE 等同 bare 且不讀 OAuth／Keychain。完整 minimal 模式無法直接沿用訂閱，是目前根本限制，不代表所有未來版本皆無解。

## 未完成門檻與正式保留

尚未實作：多 profile 共用容量與常駐分配、可審核且可更新的 catalog 來源／版本 gate、未知 CLI／managed 衝突處理、完整模型／schema／tools／images／注入與品質矩陣、真 OpenRouter 同題對照、公開 HTTPS 候選及 Mac source release。本輪不把實驗檔提交為產品 runtime，不升版、不部署 Worker。

正式唯讀覆核：49 個 core 檔吻合 0.9.11 公開 ZIP；health accepting、idle resident 2、running／queued／refill_failures 0、workers／pending 64。58 筆 Key rows、3 把有效 owner Key 保留；本輪沒有建立 API Key，個人 Codex config 與 settings／key rows 比對不變。原 checkout 擁有者的 .gitignore／AGENTS.md 變更未觸碰。

研究紀錄與計畫可作為後續整合的依據；issue 46 與完整 warm 門檻 issue 39 維持開啟。靜態文件／CI 檢查只驗此交付，不代替上述尚未執行的 runtime 門檻。

本機回歸：Bridge／tools／Windows packaging 472 passed、23 skipped；Worker relay 13 passed，產品文件／品牌／diff whitespace 通過。私有 terms 清單本機未提供，`lint_terms.py --require` 明確失敗，不視為通過；合併前由有 secret 的 PR CI 驗證。純文件收據依 D-15 不升 runtime／Mac 版本，不產生替換 release。
