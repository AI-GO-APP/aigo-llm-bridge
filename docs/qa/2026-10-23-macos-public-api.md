# Mac 公開 API 上線與交付證據

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

R-23／D-29：管理台分開顯示本機／公開 Worker／真實測試；無 Key route check 不推論，明確 Chat／Decisions 測試才計量。舊 Worker 404 提示原地更新、unknown／過期狀態與 handoff 不聲稱已部署。回歸、PR、Mac source Release、公開下載與正式安裝結果由後續實際收據補齊，未完成前不宣稱已發布。

本機共用核心／tools／Windows 共用適配／Mac platform 回歸 342 passed、23 個平台專用案例 skipped；最後增加實際模型與成本檢查後，相關管理台／證據測試 23 passed。Node Worker 12 passed；文件、版本、品牌、JavaScript 語法及 diff check 通過。本機未提供私有 terms 清單，`lint_terms.py --require` 如實失敗，待 repo-secret CI 完成，未以自造清單放行。

真實 Cocoa／WKWebView：六頁 × 淺／深色 × 1200／480px，另驗公開狀態卡、三欄／窄版測試表單、Mac 適配卡、Windows 共用適配卡與五步精靈。old_worker_warning／route_is_not_inference、真剪貼簿還原、CSV Save／Cancel、Key 清空、導航邊界、關 viewer 後 API 持續 200 通過。Windows 卡只是在 Mac WKWebView 的共用 DOM 視覺驗證，不宣稱已對 Windows 原生安裝重驗或發布。
