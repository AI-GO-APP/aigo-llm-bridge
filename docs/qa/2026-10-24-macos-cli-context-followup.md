# Mac CLI 上下文續測：Codex namespace 與 Claude 結構輸出

2026-10-24；使用者同意繼續測試。產品 Local Token Buffet Bridge，正式安裝仍為 **0.9.10-mac.1**／`26ab468b157747f1de6ea5dc3e934874b2f6bedf`，常駐 **2**、workers=pending=**64**。本輪只做實驗與收據；沒有套用候選參數、停止／更新正式服務、部署 Worker、切換登入或發布安裝包。

承接 [0.9.10 goals／技能精簡](2026-10-24-macos-codex-context.md)與 [issue 46](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/46)。goals 是長期目標／自動續做開關；並非通用的上下文清空功能。本輪進一步查工具宣告能否消失，以及 Claude 原生結構輸出是否重付上下文。

## 方法與邊界

- 本機 Mac arm64，Codex **0.163.0-alpha.11**、Claude Code **2.1.306**。
- 24 次 mock turn：Codex 15、Claude 9。隔離 HOME／CODEX_HOME 或 CLAUDE_CONFIG_DIR／XDG／空 cwd，loopback mock Responses 或 Anthropic Messages；Codex mock requires_openai_auth=false，Claude mock 只用明確假 credential。沒有轉送訂閱憑證、模型推論或 owner 對話。
- 實際 native CLI 送出的 payload 僅在 RAM 分類，保存欄位、長度、hash、工具名稱、已知 marker；原始內容／headers／events／stderr 不保存。mock 的 usage 為合成值，**JSON 的 o200k_base 近似值不是模型計費 tokens**。
- 7 次真訂閱推論 CLI：Codex 4 次直接 CLI；Claude 2 次原公開 HTTPS 加 1 次直接 CLI。全部併發 1，內容固定合成，完成後丟棄原回答。兩種 transport／模型分開，不混成速度排名；未重送任何失敗推論。
- 只有 Claude 公開兩筆有 Bridge receipt；直接 CLI 實驗沒有 public UUID／warm lease，不能冒充公開端點或常駐收益證明。真 usage 取 CLI／公開回應，本機 cache 與成本另核對 allowlist request metadata。

## Codex：仍不能完整清空，但找到再精簡的候選

目前 flags、personality=none、code_mode host／布林開關、code_mode_only、nested enabled=false、code_mode_interrupt 等實驗中，未排除 namespace 時 additional_tools JSON 都約 **2985** 近似 tokens，仍含 exec、wait、request_user_input、request_user_input_async。

官方 [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)列出 `features.code_mode.excluded_tool_namespaces`。以單次子程序參數排除 `functions`、`clock`，並明確保持 `features.code_mode.enabled=false`，可移除嵌入 exec 說明的 apply_patch／MCP resources／clock 定義；additional_tools JSON 降至約 **2426**，但外層四種工具仍在。這是 code-mode 配置領域，官方標示相關功能仍在開發中，不推定其他版本等價或穩定。

只排除 functions 約 2516；改為 direct_only 的對照反而約 3107，因定義改成直接宣告，不能把「從 nested 說明消失」當成總 token 消失。各組 input JSON 另受 cwd 等差異影響，判斷工具精簡以穩定工具區塊與 hash 為主。

也測試非互動 `codex exec --ephemeral --json --skip-git-repo-check`，使用同一模型、Bridge 固定基本指令、空 cwd 與同等技能停用。它仍送出相同四種外層工具；未排除 namespace 約 2985、排除後約 2426。**改用 exec runner 本身沒有成為純 messages／零工具入口。** ephemeral 的 rollout 檔案數均為零。

同一 gpt-6.1-sol、直接 CLI、每格 1 筆，順序為 current Chat→candidate Decisions→candidate Chat→current Decisions：

| 題型 | current input | candidate input | 減少 | current 秒 | candidate 秒 |
|---|---:|---:|---:|---:|---:|
| Chat，短 PONG | 3120 | 2630 | 15.71% | 3.3303 | 4.1645 |
| 單題 blue noul | 3257 | 2769 | 14.98% | 5.0127 | 5.7269 |

4/4 模型、格式、finish 與完整 CLI usage 通過；cache 均零。候選的 output 分別為 6／16，current 為 6／42，其中 current Decisions 含 24 reasoning tokens。每格僅 1 筆、前後分時且生成行為不同，**本輪沒有速度改善證據**。這也不是 0.9.10 公開 API 對照的延續樣本。

候選沒有動個人 config，也未進入正式 code/default；尚待可維護的設定整合、完整 schema／history／image／取消／工具拒絕回歸與版本相容性驗證。其餘 exec／wait／詢問使用者／權限／環境仍在，未驗得受支援的完整零工具設定，不修改管理員 requirements 或抽取訂閱 token 直連私有端點。

## Claude：Chat 已大幅精簡；bare 有認證限制

mock 直接重現現行 `call_claude` 的 system replacement、tools=""、restricted、空 MCP／settings sources、空 cwd 與不持久化。Chat 的一般工具清單確為空，沒有 CLAUDE.md／技能目錄 marker；system 為三個短區塊（含 Bridge 固定提示），system JSON 約 **118**、messages JSON 約 **379** 近似 tokens，仍有 system-reminder。

保留其他 Bridge 隔離 flags、只恢復預設 system 的控制組，system JSON 約 **2901**；再恢復 tools=default 的對照也載入工具定義。這些不是完整原生互動預設，更不是帳戶端實際計費，但足以確認目前的 system replacement 已去掉大量代理指令。

另加 `--disable-slash-commands` 沒有實質下降；放入一份完全合成的 user skill fixture，現行無工具路徑也沒有送出該 marker，停用 slash commands 後沒有進一步收益。結果只涵蓋此 fixture，不據此保證所有 plugins／managed 設定情境。

`--bare` mock 可令 messages JSON 降至約 **44**，system-reminder 消失，但 system 短區塊仍在。**本機 help 與官方文件都明定 bare 不讀 OAuth／Keychain、不能使用目前的訂閱登入**；本輪僅在 fake credential mock 測試，沒有把它套到真訂閱。[CLI flags](https://code.claude.com/docs/en/cli-reference)、[bare 認證與行為](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)。

原 0.9.10 公開 HTTPS、同一 Haiku 4.5，各 1 筆：

| API | input | output | 秒 | receipt |
|---|---:|---:|---:|---|
| Chat，短 OK | 562 | 60 | 2.9063 | 完整 1/1、cold=1 |
| 單題 blue noul | 3474 | 618 | 7.1330 | 完整 1/1、cold=1 |

兩筆模型／格式／成本與 receipt 相符，cache read/write 均零。Claude 沒有已驗 ready 邊界，正式仍 cold；Codex resident=2 及全機容量不變。這不是不同 provider 的同模型比較，也不能由一筆推定 SLA。

## Claude Decisions：原生結構輸出額外回合

現行自有 Decisions 使用 `--json-schema`，mock 上游會收到唯一的 **StructuredOutput** 工具。這是 CLI 的結構輸出機制，與檔案／命令執行工具不同；不能把 Chat 的 tools=[] 推論為 Decisions 上游也沒有任何格式工具。

mock 一次正確 StructuredOutput 呼叫即可完成，卻不代表真模型一定一次完成。為釐清上述較高用量，再做 1 次直接、同模型／同固定 blue noul 的真 CLI，僅在 RAM 分類 stream：

- CLI 自報 num_turns=3，結果成功且含 structured_output。
- 觀察到 **2 個不同 assistant message id**，input 分別 **1486、2180**，合計 **3666**，與 CLI 完整總 input 一致；其中一個使用 StructuredOutput。
- CLI 完整 output=**801**、耗時 **7.6797 秒**；各 assistant event 的 output usage 可能尚為 partial，不能拿其最後一筆小數值相加取代 CLI 總 output。沒有保存任何文字、tool arguments 或原始事件。
- 這是同一次 CLI 內的結構輸出流程，沒有 Bridge 重送或跨 caller 共用 thread。觀察到的 assistant 回應數亦不冒充完整 wire/API 重試追蹤。

因此 Claude Decisions 的成本不僅是初始固定 prompt；生成原生結構的多步驟也可能重付上下文。後續若優化，需驗證同模型單次結構輸出路徑，並保留 D-37 的可靠格式、語意驗證與完整 usage。不能由此宣稱 Jev 校準相同。

第一個診斷 helper 錯把唯讀 auth status 的 JSON 當成推論事件解析，於模型啟動前發生 AttributeError；已限定只分類 -p 子程序再完成上述一次真呼叫。前一失敗保留在數字收據，真推論為零，不當作模型失敗重試或丟棄壞樣本。

## 總量、保留與後續

本輪真推論 CLI **7 次**，合計 **19,478 input／1,549 output tokens**。mock 24 次均無訂閱推論；一把公開測試 Key 已撤銷，3 把原有效 owner Key 及全部既有 rows 保留。Codex 個人 config hash、正式設定不變；最後 health 接單中、idle=resident=2、workers=pending=64、無 refill failure。沒有新增背景任務或替外部使用者發動基準測試。

結論：Codex 找到約再省 15% input 的局部候選，仍有約 2.6k 短 Chat 輸入；Claude Chat 的既有精簡確實有效，Decisions 的原生結構多回合值得獨立處理。候選尚未部署，正式維持已驗的 0.9.10。完整 #39 尖峰／資源與跨平台門檻另列；本輪不以正常短題測試取代隔離／工具執行防線驗證。

完整 allowlist metadata、24 組 mock 分類、逐筆真 usage 與 helper 失敗見 [數字證據](../concurrency-evidence/macos-cli-context-followup-2026-10-24.md)。
