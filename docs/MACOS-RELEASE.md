# Mac BYO source Release：安裝、更新與發布

目前原機正式使用 [0.9.16-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.16-mac.1)，按owner明確授權的4＋4／32／32與零推論簡易驗收交付；公開包／原profile更新／保留原Key與資料見 [本輪收據](qa/2026-10-24-macos-32-operator-release.md)。未做32真推論穩定性或新壓測，#60未宣稱修復。下列0.9.12回復狀態是先前歷史，0.9.13–15失敗原件保留。

0.9.13／14／15皆已發布並完成原機更新測試，但後測有失敗，Release標prerelease並保留原附件；當時正式服務回復0.9.12，owner為minimal4＋standard4／64／64。0.9.15的99/116與回復收據見 [最新QA](qa/2026-10-24-macos-auth-preflight.md)，後續交付可靠性追蹤#60。下文0.9.12發布當時的常駐2是歷史配置，更新不覆寫owner指定的4＋4。

先前完整推論驗收的正式版本為 [0.9.12-mac.1](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/macos-source-v0.9.12-mac.1)。Codex純文字Chat profile、公開四附件、ZIP真安裝、原profile更新與同Key真API對照見 [本輪收據](qa/2026-10-24-macos-chat-minimal-release.md)。0.9.12發版當時owner常駐合計2（minimal／standard各1）及64/64；新安裝預設常駐0，Claude cold，Decisions StructuredOutput保留。完整warm放行仍追蹤issue39，本輪沒有Worker部署或Windows發布。先前 [0.9.11收據](qa/2026-10-24-macos-cli-token-release.md)留作歷史。

0.9.4-mac.1 候選整合 PR #32 的 64 併發；本輪先驗基本流程；owner 後續授權本機 Claude 64 併發測試。交付狀態見 [Mac 併發收據](qa/2026-10-23-macos-concurrency.md)。

0.9.5-mac.1 在其上修正 LaunchAgent 256 檔案描述符上限造成 64 併發只約 40 筆可執行的問題；公開 HTTPS 的 64 名額需另以 `byo_setup.py deploy` 原地更新同一 Worker。

Mac 現行渠道為 `macos-source-v<Mac VERSION>` 的 GitHub Release。它交付現行 BYO source ZIP、SHA256、來源 manifest 與 self-test；包含 Cocoa／WKWebView 管理台及 source 安裝器，需 Python 3.12+。這是支援的 Mac 發布格式；不宣稱提供公證 .app／DMG、自動簽章 feed 或 Windows Velopack 更新。

## 從公開 Release 安裝

1. 在 [Releases](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases) 選 `macos-source-v…`，下載 `aigo-llm-bridge-macos-source-<version>.zip`、其 `.sha256` 及 `macos-source-manifest.json`。不要選歷史 desktop-macos 包。
2. 在下載目錄執行 `shasum -a 256 -c <下載的zip>.sha256`；必須 OK。manifest 的 version／commit／sha256 對應該 Release 來源。
3. 解壓，在 `aigo-llm-bridge` 目錄開 Terminal，執行 `sh Install.command`（或 `python3 tools/install.py`）。可明確指定 `--install-root`，不需要 sudo。不繞過作業系統安全提示；若 Finder 無法直接執行，使用上述可檢查的 Terminal 指令。
4. 開啟安裝目錄 `Bridge.command`，依 [Mac 五步設定](MACOS-SETUP.md) 完成本人 CLI、Cloudflare、自有 Worker、電源同意與真 HTTPS／KEY 交付。只有已完成者日常啟動才略過。完整資料位置與 CLI 見 [source 安裝](CROSS-PLATFORM-INSTALL.md)。

`source-install.json` 的 `source_commit` 取自 ZIP 內 `source-release.json`；解壓位置即使位於其他 git repo 內也不會誤記外層 commit（0.9.6-mac.1 起）。

ZIP 不含使用者資料或憑證，也不附 Python runtime。安裝器建立專用 venv、安裝依賴、複製來源與文件；`source-install.json` 記錄版號、原 Release commit、data-dir 及來源位置。解壓來源保留在自己選定的位置，供日後明確來源更新；資料始終在安裝 profile，不在下載 ZIP。

## 更新既有 Mac

下載、驗 hash、解壓新包，不重新跑 Cloudflare 部署或建立替代 KEY。從原安裝 `source-install.json` 讀出 `python`／`app`／`install_root`：

```sh
BRIDGE_ROOT="$HOME/Library/Application Support/AIGO LLM Bridge"
BRIDGE_PY="$BRIDGE_ROOT/runtime/bin/python"
BRIDGE_APP="$("$BRIDGE_PY" -c 'import json,sys; print(json.load(open(sys.argv[1]))["app"])' "$BRIDGE_ROOT/source-install.json")"
"$BRIDGE_PY" "$BRIDGE_APP/tools/mac_service.py" update --install-root "$BRIDGE_ROOT" --source "/path/to/new/aigo-llm-bridge"
```

工具先 pause／wait-idle、停止原 LaunchAgent、更新相同 data-dir、重啟並驗 HTTP 新版；失敗走回復。手動 runtime 需先在管理台「結束 Bridge」，不能強殺正在工作的個人 CLI。更新後重讀 manifest，確認版號與 Release commit，使用同一原 KEY 驗外部 models／chat／cost。URL、device ID、原 KEY rows、模型與容量保留。`rollback` 排空後回上一個程式 manifest，不回復／覆蓋新 DB；若版本改了不相容依賴，依上一版 requirements 恢復 venv。

## 維護者發布

1. 新增 R／D 與 QA，更新 VERSION／常數／CHANGELOG、Mac 操作與雙平台入口；Windows release-target／policy 不跟著改。
2. 本機跑維護閘門、真 Cocoa 六頁與五步畫面、原生剪貼簿／CSV／視窗關閉後服務、全機互斥與乾淨停止。首次權限／登入使用 fake 或本人操作，不改 owner 電源／鎖定來驗收。
3. PR 以 main 為基底，所有必要 CI 通過後合併。Mac `byo-source` 會建現行 BYO 包、從 ZIP 實際安裝並驗服務／互斥／停止；legacy verify 僅為歷史回歸，不是發布包。
4. 在合併的 clean main 執行 `Mac BYO source release`（`macos-source-release.yml`，workflow_dispatch）。它重新跑 Mac 驗收、核對 commit／version／dirty=false／redistributable／hash，再建立不可覆寫的 Mac Release。相同版本已存在時應核對原 bytes，不能刪除或覆寫 Release 來規避錯誤。
5. 匿名下載公開四個附件，驗 hash／來源，從下載 ZIP 在 Mac 實際安裝及啟停。更新 owner 既有安裝並驗原設定／KEY／URL、真外部 HTTPS／成本；測試 KEY 撤銷，owner KEY 保留。
6. 把 Release URL、來源 SHA、附件 SHA256、CI URL、公開回讀、下載安裝、已安裝升級與外部驗證記入 QA／ACCEPTANCE。文件收據 PR 不升版，與已發布 immutable runtime 分開。

發布權限只限 Mac GitHub Release，不部署任何安裝者 Worker、不變更 Windows 更新政策、不操作其他 Cloud 專案。根 release.yml 持續略過 Mac 版號，避免把歷史 worker 附件當作現行 Mac 安裝包。

0.9.7-mac.1 已完成 #36 階段 0–2、公開發布及原安裝升級。[效能門檻](PERFORMANCE-PLAN.md)、[實作與負面結果](qa/2026-10-24-macos-queue-decisions.md)及[發布收據](qa/2026-10-24-macos-queue-release.md)分層記錄，warm CLI 不隨本批啟用。

0.9.10-mac.1 已依 issue 46 精簡 Bridge Codex goals／技能上下文；完整診斷、負面測試與公開發布／原安裝同題對照見 [上下文收據](qa/2026-10-24-macos-codex-context.md)。原 Worker 與 2/64 profile 不因上下文修補重建。

0.9.11-mac.1 已完成 D-42 的合併、發布、公開下載安裝與原 profile 更新。後續 schema 去重／thinking-off 只列研究候選，未加入此已發布程式；狀態見 [本輪收據](qa/2026-10-24-macos-cli-token-release.md)。

Mac0.9.13-mac.1候選加入D-46連線重用／batch8；目前交付階段見 [本輪收據](qa/2026-10-24-macos-relay-batch-release.md)，不能以source測試代替已發布／正式安裝。該輪owner為4＋4／64／64，0.9.12發版時的2常駐也是歷史配置；現行0.9.16指定4＋4／32／32見本文頂端，更新不自動覆寫其他profile。
