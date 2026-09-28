## 這個 PR 做了什麼

<!-- 使用者會看到什麼差別。一兩句即可。 -->

## 版本與升級影響

- [ ] 已跑 `python tools/version.py --bump patch|minor|major`(只動 `.github/`、`spikes/`、`tests/` 可免)
- [ ] `CHANGELOG.md` 的新段落已寫好,含「升級影響」(Bridge／表／環境變數／worker／客戶端各要不要動)
- [ ] 有破壞性變更的話寫在段落最前面,並含「破壞性」字樣

## 檢查

- [ ] 改了 `clients/` 就跑過 `python tools/sync_clients.py`
- [ ] `hosted`、`worker`、`tools/tests` 的 pytest 通過
- [ ] 沒有任何金鑰、token、`.env`(`python tools/scan_secrets.py`)
- [ ] 沒有任何特定客戶、租戶、專案或人名(含 commit 訊息與作者名)
- [ ] 行為改了,對應的文件也一起改了

## 怎麼測的

<!-- 本機單元測試、docs/12 的端到端、平台上的驗證……寫實際做了什麼。 -->
