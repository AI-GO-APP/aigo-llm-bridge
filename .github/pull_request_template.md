## 這個 PR 做了什麼

<!-- 使用者會看到什麼差別。一兩句即可。 -->

## 版本

- [ ] 已跑 `python tools/version.py --bump patch|minor|major`(只動 `.github/`、`spikes/`、`tests/` 可免)
- [ ] `CHANGELOG.md` 的新段落已寫好;有破壞性變更的話寫在段落最前面,並含「破壞性」字樣
- [ ] 需要部署者或使用者動手的步驟(補表、改環境變數、重新部署、換 worker)已寫進 CHANGELOG

## 檢查

- [ ] 改了 `clients/` 就跑過 `python tools/sync_clients.py`
- [ ] `hosted`、`worker`、`tools/tests` 的 pytest 通過
- [ ] 沒有任何特定客戶、租戶、專案或人名(含 commit 訊息)
- [ ] 文件與 `SKILL.md` 的指引跟著行為一起改了

## 怎麼測的

<!-- 本機單元測試、tools/e2e_auto.py、平台上的端到端……寫實際做了什麼。 -->
