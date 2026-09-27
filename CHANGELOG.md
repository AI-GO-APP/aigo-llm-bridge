# Changelog

格式參考 [Keep a Changelog](https://keepachangelog.com/),版本號遵循 [SemVer](https://semver.org/)。
0.x 期間 API 可能變動,每次變動都會寫在這裡。

## [Unreleased]

### Added
- repo 骨架:README、術語表(CONTEXT.md)、架構(docs/01)、使用邊界(docs/02)
- `tools/lint_terms.py`:檢查 repo 內容與 commit 訊息是否出現不該出現在通用套件的字詞;
  清單由 CI 變數或本機 `.banned-terms` 提供,輸出不回顯命中的詞
- CI:禁字檢查、Python 語法檢查
