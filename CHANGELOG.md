# Changelog

格式參考 [Keep a Changelog](https://keepachangelog.com/),版本號遵循 [SemVer](https://semver.org/)。
0.x 期間 API 可能變動,每次變動都會寫在這裡。

## [Unreleased]

### Added
- repo 骨架:README、術語表(CONTEXT.md)、架構(docs/01)、使用邊界(docs/02)
- `tools/lint_terms.py`:檢查 repo 內容與 commit 訊息是否出現不該出現在通用套件的字詞;
  清單由 CI 變數或本機 `.banned-terms` 提供,輸出不回顯命中的詞
- CI:禁字檢查、Python 語法檢查、hosted-echo 單元測試
- P1 實測腳本:`spikes/cli-latency`(S1)、`spikes/hosted-echo`(S2–S4 共用的模擬服務)、
  `spikes/custom-app-client`(S2、S3 的 Custom App)、`spikes/cold-poll`(S4)
- `tools/deploy_hosted.py`、`tools/hosted_env.py`、`tools/aigo_api.py`:部署 Hosted App 與安全地更新環境變數
  (先讀現況再合併;共用池租戶不送 `resources`;錯誤訊息不回顯值)
- docs/01 §5:S1、S3 實測數字與由此得出的設計決定;S2 以標頭確認可行並記下 CSP 限制

### Changed
- owner / caller user 改以平台使用者 id(`ctx.user_id`)識別,不再以 email
