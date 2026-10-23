# 參與開發與維護

先讀 [AGENTS](AGENTS.md) 與[產品文件入口](docs/README.md)。現行產品為 Windows／macOS BYO Cloudflare LLM Bridge；`hosted/`、`worker/`、`desktop/` 及編號 01–13 文件是歷史產品線。安裝依 [README](README.md) 分流；Agent 使用 [安裝 prompt](docs/AI-AGENT-SETUP.md)。

## 分支、驗證與合併

使用功能分支／工作樹提出 PR，不直接推 main。變更功能時在同一 PR 更新受影響的需求、架構、schema、API、設計、決策與驗收。新需求／取捨依序使用未占用的 R／D 編號；主線已有其他平台合併時保留其修補、決策與發布紀錄，整合後重新驗證。

```sh
python tools/check_product_docs.py
python -m pytest desktop_bridge/tests packaging/windows/tests tools/tests -q
node --test cloudflare/test/relay.test.js
node --test packaging/windows/tests/platform.test.js
python tools/version.py --check
python tools/sync_clients.py --check
python tools/scan_secrets.py
python tools/lint_terms.py --require
```

私有 terminology 清單只取本機 `.banned-terms` 或 repository secret `BANNED_TERMS`，不得輸出、捏造或用空清單放行。缺清單時本機明確記錄，由具 secret 的 CI 完成必要 gate。平台原生安裝／更新／UI 另跑對應 workflow，不能用其他平台或 fake 結果代替。

所有必要 CI 成功、維護者完成語意與隱私／資料檢查後才合併。可自審自己的 PR，但需在 PR 清楚記錄測試與證據。依 [CI/CD](docs/CI-CD.md) 使用 squash merge；保留已發布 tag 與不可變附件，不改寫公共歷史。

## 版本與發布

- Windows Setup 使用 `packaging/windows/release-target.json`，依 [Windows Release](docs/RELEASE.md) 獨立發布與 signed policy；不因 Mac 升版修改它。
- Mac 使用 `VERSION` 的 Mac source 版號、`packaging/macos/build.py` 與 [Mac Release](docs/MACOS-RELEASE.md)。發布 main 的現行 BYO ZIP，必須有 clean commit／SHA256／真下載安裝與 owner 更新收據；不使用 legacy desktop 包。
- 共用版本修改使用 `tools/version.py --bump <version>` 同步四常數與 client 副本並更新 CHANGELOG。Mac 版號也須通過相對 main 的新版本閘門。
- 純 Markdown／允許的 QA 圖片收據不用升二進位版本；runtime、installer 或可執行 assets 不能偽裝成文件免除 gate。
- 發布與升級是不同階段。確認公開匿名下載、套件來源、已安裝版本、原 device／URL／KEY／模型／metadata 保留與真 HTTPS 後，更新 repo QA／ACCEPTANCE。

## 隱私與操作邊界

原始 request／response、KEY、token、密碼、DPAPI／Keychain 或安裝者 profile 不進 repo、包或報告。程式碼與檔案路徑皆納入 terms／secret 檢查；作者姓名須符合公開 repo 規則，已核對的身分別名使用 `.mailmap`，不改寫歷史。

驗收使用合成內容與專用測試 KEY，結束撤銷；既有 owner KEY 保留，不建立替代 KEY 冒充升級保留。供應商 CLI 登入、Cloudflare OAuth、裝置 secret、client KEY、管理 token 各自獨立。不操作個人 CLI 視窗，不偷偷改 owner 電源／鎖定或部署 Worker。平台與外部變更只依本次使用者授權執行。
