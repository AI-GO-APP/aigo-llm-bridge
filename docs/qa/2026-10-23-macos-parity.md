# Mac 0.8.0 source 同步驗收

狀態：本機 source 適配、原生 renderer 及現有 Mac 安裝更新／外部 HTTPS 通過。來源 `4445670`；未發布 Mac release，未驗項不得當成通過。

## 來源及範圍

- Windows 0.7.3 主線 `d3f2707` 及 0.8.0 候選 `22c843c`。0.8.0 分支尚未合併，不稱為已發布。
- 原 Mac 安裝 `0.6.6-mac.2`；同步六頁設計、首次設定、BYO／KEY／HTTPS 交付、WKWebView、AC sleep 與來源更新。
- 沿用原 Mac profile，不操作遠端 Windows、其他 Cloud 專案、個人 CLI 登入或鎖定設定。
- 電源寫入、授權取消及還原使用 fake adapter；本機只讀現有設定。真 OAuth／新 Worker 部署不因升級重做。

## 驗證紀錄

| 檢查 | 本輪結果及範圍 |
|---|---|
| Python | `pytest desktop_bridge/tests packaging/windows/tests tools/tests desktop_platform/macos/tests -q`：241 passed、4 skipped。Mac adapter、AC-only 同意／取消／備份／還原、pending 恢復、原生操作邊界、同 KEY proof、更新失敗回復均包含；Windows OS 測試留在 Windows。 |
| Node | relay 7 passed；Windows platform seam 2 passed。 |
| 版本／文件／機敏掃描 | `tools/version.py --check`、`tools/check_product_docs.py`、`tools/scan_secrets.py`、`git diff --check` 通過。 |
| 必要禁字檢查 | 本機 `tools/lint_terms.py --require` 沒有私有清單；由有 repository secret 的 [PR CI](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39893158743) 完成 lint-terms／secrets／docs／version-bump 等檢查並通過，不虛構清單或降低規則。 |
| 真 WKWebView | `tools/verify_macos_console.py`：六頁、五步精靈、Mac 卡，light／dark × 1200／480px 共 48 個版面變體；全頁無橫向溢出。實際渲染後檢視代表圖，並非只檢查 CSS 字串。 |
| 原生橋接 | 前端呼叫真 pbcopy 並讀回中文；保留 CSP `script-src 'self'`，固定三個 closure 介面，不開 unsafe-eval；外部導覽在 WKNavigationDelegate 阻擋。 |
| 原生 CSV | 真 NSSavePanel Cancel，以及原生 panel 自動選中文檔名後 Save，匯出 metadata／0.012345 USD 回讀通過。chooser 的回傳與取消亦有獨立測試；不是人工點選證據。 |
| 視窗生命週期 | viewer 關閉後本機 `/health` 仍為 200；關閉精靈清除 KEY 欄位。 |
| 隔離真安裝 | source installer 實際安裝 Cocoa 依賴，安裝後 headless `/health` 為 0.8.0-mac.1，Mac 及產品文件隨附。沒有新建 Worker。 |
| 既有 Mac 真升級 | `tools/verify_macos_upgrade.py --apply`：0.6.6-mac.2 → 0.8.0-mac.1；device ID、固定 URL、原帳戶／Worker、全部既有 KEY 完整 rows、七模型映射、預設模型及四路容量一致。 |
| 同 KEY 外部驗證 | 同一臨時 Codex KEY 在升級前後 GET models 200；更新後一般 chat 200，5.733 秒，model=openai/gpt-6.1-sol，usage.cost=0.008446 USD 牌價估值，請求前後系統皆回報鎖定。 |
| 結構化／工具／邊界 | 外部 JSON schema 200；指定工具提案 200／arguments 合規且未執行主機工具；相同 request ID 回相同結果且不新增 DB request；temperature 回 400 unsupported_parameter；第三方交付欄位完整。 |
| 測試 key 清理 | 升級跨版本臨時 key 撤銷；原 owner service keys 完整保留，不建立替代長效 KEY 冒充原 KEY。 |

![Mac 設定與來源更新卡](assets/macos-0.8.0-platform-dark.png)

![Mac 首次設定與電源同意](assets/macos-0.8.0-onboarding-light.png)

## 已知邊界與操作紀錄

- 實際部署、OAuth、管理員電源寫入及 Claude 訂閱真推論沒有重做。既有 Codex／Keychain／Relay 實際使用；電源改動及取消以 fake adapter 驗證，不以此聲稱工作站已套用新電源設定。
- 現有有效服務不因新精靈未完成而被阻擋；本人仍須明確同意電源步驟及完成 KEY 保存／交付勾選，不能為了驗收偽造完成紀錄。
- 某輪 unattended Save 測試曾卡在額外對話框，只結束該測試程序，未動正式 Bridge；該輪未能恢復原剪貼簿，已告知 owner。後續改為複製檢查後立即還原，再做 modal 測試。
- 來源更新不是 Windows 簽章 feed；沒有 Mac .app／DMG 發布、強制更新政策或 OS 登出後供應保證。
- [Mac CI](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39893158616) 的 legacy verify 與新 BYO source／真 Cocoa renderer 皆通過。首輪 Windows runner 找出兩個 Mac 測試對 OS 的假設：Python 解譯器可有 `.exe`，POSIX update lock 不在 Windows 執行；已修正測試邊界並重新執行，不將失敗隱藏成 Windows 功能通過。

原始內容與完整 KEY 只在 RAM。報告不含 endpoint、帳戶 ID、管理 token 或原始模型輸出。
