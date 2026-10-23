# Mac 公開 API 上線與交付證據

狀態：原 Worker 部署、公開 API 全鏈驗收、管理台修補、PR 合併、Mac Release、公開下載安裝與 owner 正式更新均完成。使用方專案內的整合及業務閾值驗收仍由呼叫端執行，不冒稱已存取其環境。

## 原地部署與外網驗收

2026-10-23，owner 明確授權既有 Mac profile 的同一個 Worker 更新與合成推論驗收。本機原已安裝 `0.9.1-mac.1`，source `e3c09bb7cb478220413f5e2c75dc35183e689675`；新版 Worker 範本 SHA256 `ed71f7c1e76f30045105233219e72761a13017d9f0bad7f7014ebc5379c610ce`。公開 Worker 原為 `0.3.4-relay`，新四路徑 404；不是 client Key 問題。

使用專案暫存工具 Node 22.23.4／Wrangler 4.152.0，驗證原綁定帳戶、保存 deployments metadata、pause／wait-idle，以已安裝版本 helper configure／publish 原地更新。一般更新沿用配對，不重寫 DEVICE_KEY。先前版本 `5549d4e3-6145-46d2-89dc-0db748f6acc6`；本次部署 version `a3a35c9d-0227-4355-a754-51592ba833ad`。deploy 命令完成後一度仍回舊邊緣版本，後續實際核對 health／header 均為 `0.9.0-relay`，才開始推論驗收。

外部 HTTPS 直呼公開入口，真路徑為 client→Worker→Relay→Bridge→Codex CLI→JSON 解析。全部使用合成內容，未使用假 adapter、CLI 切換、電源或鎖定更改。結果：

| 項目 | 結果 |
|---|---|
| models／model-capabilities | GET 200，選定模型確實存在 |
| refresh | POST `{}` 200，requests row count 不變，沒有推論 |
| Chat | 200，PONG／實際 model `openai/gpt-6.1-sol`；7.805 秒，USD 0.0026072 |
| Decisions 三題 | 200，noul 0–1、choice 合法選項、score 0–2；20.264 秒，實際 model 相同，USD 0.028246 |
| 明確 Decisions probe | 200，有 answers、實際 model 與 USD 0.009052 |
| Decisions jobs | POST 202→GET completed 200，有 answers、實際 model、USD 0.009362 |
| UUID 去重／receipt | 同 UUID 重送不新增 request row／不再推論；已完成成本與 calls 逐項一致 |
| 不完整計量 | job 執行中 receipt complete=false、calls_started=1；完成後 complete=true、completed=1，未把執行中視為免費 |
| 錯誤 | 非等價 temperature 400 unsupported_parameter；無效 Key 401 |
| 重啟 | 正常排空重啟，同一臨時 Key models 200、新路由 200 |
| 清理 | 本 session 臨時 Key 撤銷後外網 401；原 owner 全部 Key rows、URL、device、帳戶／Worker、模型與容量一致 |

只保存 allowlist metadata；測試 Key、原始 prompt／response 只在 RAM，不進腳本或收據。沒有存取使用方專案環境，因此這是公開 API 全鏈驗收，不冒稱已驗使用方應用程式或其答案解析。Jev 為一般 LLM 模擬，業務機率閾值仍需呼叫端獨立校準。

## 產品修補與發布

R-23／D-29：管理台分開顯示本機／公開 Worker／真實測試；無 Key route check 不推論，明確 Chat／Decisions 測試才計量。舊 Worker 404 提示原地更新、unknown／過期狀態與 handoff 不聲稱已部署。以下分別記錄回歸、發布及正式安裝證據。

本機共用核心／tools／Windows 共用適配／Mac platform 回歸 342 passed、23 個平台專用案例 skipped；最後增加實際模型與成本檢查後，相關管理台／證據測試 23 passed。Node Worker 12 passed；文件、版本、品牌、JavaScript 語法及 diff check 通過。本機未提供私有 terms 清單，`lint_terms.py --require` 如實失敗，待 repo-secret CI 完成，未以自造清單放行。

最終全量回歸再次 342 passed／23 skipped。[PR #30](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/30) 的 15 項 checks 全成功，包括 repo-secret lint-terms、Mac 真 WKWebView／ZIP 安裝，以及 Windows 可拋棄 runner 的共用核心／原生安裝更新相容性；未發布 Windows。合併來源 `119329da4fa0e3cd08de2fd1dfd60082a6b056b5`，Mac source `0.9.3-mac.1`。原 immutable Release 保留。

真實 Cocoa／WKWebView：六頁 × 淺／深色 × 1200／480px，另驗公開狀態卡、三欄／窄版測試表單、Mac 適配卡、Windows 共用適配卡與五步精靈。old_worker_warning／route_is_not_inference、真剪貼簿還原、CSV Save／Cancel、Key 清空、導航邊界、關 viewer 後 API 持續 200 通過。Windows 卡只是在 Mac WKWebView 的共用 DOM 視覺驗證，不宣稱已對 Windows 原生安裝重驗或發布。

## 已發布 Mac source Release

[發布 run 39943728710](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39943728710) 成功，重新跑主線核心、真原生 renderer 與 ZIP 安裝／生命週期，再發布 [macos-source-v0.9.3-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.3-mac.1)。來源為上述合併 SHA，dirty=false／redistributable=true；未覆寫舊 Release，未發布 Windows 或修改 Windows policy。

四個公開附件均已匿名下載，ZIP、SHA256、manifest 與 self-test 大小吻合。ZIP 1,486,897 bytes；SHA256 `4dfa4719eaee860fe3e0a7da6369a5c74d5da8e447c4ce71fd93bd5e23b9086e`，同時與 manifest 及 .sha256 檔一致。

## 下載包實際安裝、正式更新與回復連線

先以同一臨時 Key 確認原服務 models 200，再透過原 mac_service pause／wait-idle／stop。以匿名下載 ZIP 的 Install.command 在隔離目錄真安裝：source provenance、已安裝 API 版本、固定全機鎖、第二 profile 被拒且無 DB、正常停止後 API 關閉通過。此過程未偽造單機鎖，也未讓第二套和 owner runtime 同時執行。

owner Bridge 明確停止後，公開 health.device_online=false、合法 Chat 回 503，request row count 不變，沒有推論。正常 start 後，原測試 Key 公開 models 200，確認重新連線；再以已下載並驗 hash 的 source 執行正式 mac_service update，沿用原 install-root／data-dir。

- 正式已安裝 `0.9.3-mac.1`，source `119329da4fa0e3cd08de2fd1dfd60082a6b056b5`；53 個已安裝 Python／JS／CSS／HTML 與公開 ZIP 逐檔相同。
- 原 device、URL、Cloudflare account／Worker、原全部 Key rows、模型／預設、relay 設定與推論容量逐項一致；沒有輪替 owner key、重新登入、改電源／鎖定或重部署 Worker。
- 新版已安裝 public route checker 對真外網回 routes_reachable、Worker `0.9.0-relay`、online=true；此檢查不推論。
- 已安裝版本再驗真公開 Chat PONG 200，實際 `openai/gpt-6.1-sol`、USD 0.008444；Decisions noul 200，實際模型一致、USD 0.009136；兩者 receipts 成本一致、complete=true／1 started／1 completed。
- 正式版本正常重啟後，同一測試 Key 公開 models 200，所有原設定／Key 比對仍一致。臨時 Key 最後撤銷且外網 401，owner 原有服務 Key 保留有效。

關 viewer X 保持背景及明確停止行為由本輪真原生驗收與上述公開離線測試共同覆蓋；Worker 更新及 Bridge 停止／恢復均實測重新連線。未改主機網路設定來製造斷網，不把停止／恢復冒稱為實體 Wi-Fi 故障驗收。
