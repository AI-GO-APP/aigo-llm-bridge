# CI/CD 與平台責任

所有平台共用 `python tools/lint_branding.py`，檢查產品文字及 repo 連結；Windows 原生 renderer 另外檢查實際頁面標題、側欄與頁面文字。識別與既有安裝相容性契約見 [BRANDING](BRANDING.md)。

本文件參照 AI EA 的分平台、來源／包／宣布／安裝證據分層，描述 **Bridge 自己的實作**。不複製 AI EA Cloud 的授權、Supabase、發布 RPC 或跨平台 UUID 協定；本專案沒有中央 Supabase，BYO Worker 也不是軟體更新站。

## 渠道與版本來源

| 項目 | 正本／責任 |
|---|---|
| Windows 原生安裝包 | `packaging/windows/release-target.json`：semver、windows/x64/internal、固定 pack ID；Windows 維護者建置、實機驗收及發布。 |
| 共用核心／舊 ZIP | 根 `VERSION`、對應平台 build；不以 Windows 安裝器升版帶動 Mac／核心版本。 |
| Mac | `VERSION` 的 Mac 版號；`packaging/macos/build.py` 封裝現行 BYO source，`macos-source-release.yml` 發布；[Mac 手冊](MACOS-RELEASE.md)。Windows 通過不等於 Mac 已驗。 |
| 安裝者 Worker | 安裝者自己的 account／device profile／BYO 工具；不由發布方 Actions 部署。 |
| 公開更新 | GitHub Windows 固定 signed policy＋每版 immutable assets；不需要安裝者 GitHub／Cloudflare token。 |

## Workflows

| Workflow | 觸發／runner | 做什麼 | 不能聲稱的事 |
|---|---|---|---|
| `ci.yml` | PR／main，Ubuntu | Python syntax、產品文件覆蓋、歷史產品回歸、同步副本、terms／secrets、版本閘門 | 不代表 Windows 安裝／GUI／Cloud 成功。 |
| `windows-installer.yml` | 相關 Windows／core 路徑 PR／main；可手動；Windows 2025 | 固定 Python 3.14.9／Node 24.22.1／.NET 8／vpk 1.2.161／鎖檔；核心與 Windows 測試、relay／adapter；真 Setup→A→B、native renderer、備份／強更新；最後在拋棄 runner 套用／還原真 AC 計畫 | 無使用者 OAuth、真訂閱、外部 BYO inference，也不驗 owner 桌面待機。 |
| `windows-installer-publish.yml` | main 手動，package=Windows，announce=Ubuntu | 重做 package gates，clean commit 封裝；預設 announce=false；true 才有發布權限與獨立 environment secret | 建置 artifact 不等於已宣布，宣布不等於使用者已升級。 |
| `desktop-windows.yml` | 自己的 paths／手動／workflow_call | 舊 Windows ZIP 及 source manifest 的 BYO package／指南 smoke | 不是目前 Windows Setup 的宣布入口。 |
| `desktop-publish.yml`、`release.yml` | 各檔案實際觸發條件 | 歷史／共用產品渠道，保留相容 | 不可拿來替代 Windows installer policy。 |
| `desktop-macos.yml` | Mac runner，PR／main／workflow_call | 現行 source／原生 renderer、現行 BYO ZIP 真安裝及互斥／停止；歷史回歸另 job | 發布只取 macos-byo-source artifact，不把 legacy ZIP 當新版。 |
| `macos-source-release.yml` | main 手動，先 Mac runner 驗收，再 Ubuntu announce | 核對 clean main commit／版本／hash，發布 macos-source-v… 及 checksum／manifest／self-test | 不發布 Windows、不部署 Worker；發布後仍驗公開下載與 owner 更新。 |

現行 runner／pin 值以 workflow、`requirements-lock.txt` 為正本；本文件與它們同 PR 更新。fork PR 不能取得正式簽署私鑰；`BANNED_TERMS` 缺失時依 workflow 的 fork 規則處理，不能把秘密清單印到公開 log。

## 本機驗證順序

```powershell
python tools/check_product_docs.py
python -m pytest desktop_bridge/tests packaging/windows/tests -q
node --test cloudflare/test/relay.test.js
node --test packaging/windows/tests/platform.test.js
python tools/lint_terms.py --require
python tools/scan_secrets.py
python tools/verify_installer_update.py --output <全新隔離輸出目錄> --vpk <固定 vpk>
```

完整工具回歸另跑 `python -m pytest tools/tests -q`；含 shell 合約的測試需實際 Git Bash／Ubuntu，不把 WSL 缺失當作產品錯誤，也不能直接略過未釐清失敗。不可分發 LocalProbe 可用 dirty tree 迭代；發布包必須 clean commit。隨附文件必須 tracked，避免把本機漏提交的指南帶進包。

原生電源探針 `tools/verify_windows_onboarding.py` 只允許 `GITHUB_ACTIONS=true` 且 `RUNNER_ENVIRONMENT=github-hosted` 的 Windows runner；不對 owner 工作站開一個「測試」旗標就改永久電源。它是避免誤操作的執行護欄，不是防止惡意環境變數的安全邊界。探針使用新目錄、保存原值、驗證鎖定登錄與螢幕／按鍵未變、finally 還原／移除專用計畫；模擬 DC 切換另由 fake adapter 驗，實體拔插／闔蓋待安裝者實機驗收。

## 不同層級的放行條件

1. **source**：需求／schema／API／設計／decision／onboarding／操作文件同步；單元與整合回歸通過。
2. **native verified**：真包 self-test、隔離 Setup／A→B／重啟／KEY／URL／metadata；權限類另註實際 OS 或 fake。
3. **merged**：功能分支 PR，正確 target CI 全綠，squash merge 到 main。資料／隱私／原生權限／雲端帳戶由 reviewer 檢查，不只看 coverage。
4. **built/staged**：從 clean main commit 建，artifacts.json、self-test.json、版本／pack ID／來源／公鑰／hash 一致；不含 `.desktop-data`、使用者 `.wrangler`、DPAPI、私鑰或 raw I/O。
5. **announced**：發布器驗公開匿名回讀與簽署 policy；序號遞增、不可覆寫同版／降 floor；結果另記 release receipt。
6. **installed-verified**：使用既有裝置／profile 的日常更新入口，核對新版、原 URL／KEY／device／metadata／訂閱與啟動。不驗外網就明列「外網未驗」，不以 HTTPS 安裝檔下載冒稱 LLM HTTPS 通過。

任何階段失敗保持原已宣布渠道；不可用盲目重跑、覆寫已發布附件、換公鑰／帳戶或刪資料規避。若已宣布後出錯，用更高版本修復，見 [Release 故障手冊](RELEASE.md)。純文件收據 PR 可不升二進位版本；程式／包改動需要對應 Windows 或 core 版本，不冒用另一平台版號。

## Secrets、留存、維護

- Actions `contents:read` 預設；只有 Windows announce job `contents:write`，concurrency 不取消已開始的發布。
- repo variable `BRIDGE_WINDOWS_UPDATE_PUBLIC_KEY`；`windows-internal` environment secret `BRIDGE_WINDOWS_UPDATE_PRIVATE_KEY`。`BANNED_TERMS` 為掃描秘密；不是更新／推論憑證。
- 不把 Cloudflare account token、DEVICE_KEY、provider auth、client KEY 或 Windows 使用者資料放進 CI。測試只使用臨時 signer／合成 profile。
- QA artifact 只保存 allowlist 結果；GitHub artifact 保留期依 workflow／repo 設定，不把它當永久交付。永久產品驗收寫 repo `docs/qa/`，且去除憑證／個人資料。
- pin 升級、runner 變更、UI adapter、installer hook、policy schema、公鑰輪替需相對應原生閘門。正常發布沿用更新 signer；丟失／疑似洩漏 signer 先停止宣布並單獨提出可信遷移，不自動信任新公鑰。

發行者操作細節、首次配置、policy 續期／強制更新、回復與完成 checklist 見 [RELEASE](RELEASE.md)。

## Windows 0.8.1 安全閘門

詳見 [SECURITY](SECURITY.md)。Windows hash-lock 安裝、固定 Actions SHA、builder runtime baseline、每日／release 前 OSV（Python、Wrangler 全鎖檔與 Velopack）採 fail-closed；原生 package self-test 包含實際 Python／OpenSSL／certifi 與 CA SHA256。這些檢查不部署 Worker 或發布 Mac。
