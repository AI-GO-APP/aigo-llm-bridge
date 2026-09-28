# 參與開發與維護

這個 repo 同時是**套件**(Bridge、worker、呼叫端)與 **Skill**(`SKILL.md` + `docs/`)。
使用者端的每一份安裝都是 `main` 的鏡像,合併進 `main` 的東西會在下一次更新檢查時自動送到所有人手上。
所以流程只有一條:**分支 → PR → 檢查通過 → 合併**,不直接推 `main`。

## 1. 一次變更的完整流程

```bash
git switch main && git pull --ff-only
git switch -c fix/stream-timeout-message          # 分支前綴見下表

# … 改程式、文件 …

python tools/sync_clients.py                        # 改了 clients/ 才需要
python tools/version.py --bump patch                # 或 minor / major,見 §3
# 在 CHANGELOG.md 新的 [x.y.z] 段落寫下這一版的變更(§4)

cd hosted && python -m pytest -q && cd ..
cd worker && python -m pytest tests -q && cd ..
python -m pytest tools/tests -q
python tools/version.py --check
python tools/lint_terms.py --commits                # 本機有 .banned-terms 時才檢查得到

git push -u origin fix/stream-timeout-message
gh pr create --fill                                  # 會帶出 PR 範本
```

| 分支前綴 | 用途 | PR 標題範例 |
|---|---|---|
| `feat/` | 新功能、新文件章節 | `feat: 串流支援 tool calls(0.3.0)` |
| `fix/` | 修 bug、修錯的文件 | `fix: stream_timeout 事件漏帶 job_id(0.2.1)` |
| `docs/` | 只改文件措辭、不改行為 | `docs: 疑難排解補上 CSP 案例(0.2.1)` |
| `chore/` | CI、測試、spikes,**使用者拿不到的東西** | `chore: worker 測試加 macOS` |

PR 標題結尾帶上新版本號,合併後一眼就能對回 CHANGELOG。

## 2. 合併規則

- **每個 PR 至少一位維護者看過**;自己開的 PR 可以自己合,但請在 PR 裡寫清楚測過什麼。
- CI 全綠才合併(`lint-terms`、`python-syntax`、`tests`、`hosted`、`worker`、`skill`、`version-bump`)。
- 合併方式用 **Create a merge commit**,保留分支上的 commit,版本號對得回 PR。
- 合併後 `release` workflow 會自動打 tag `vX.Y.Z` 並建立 GitHub Release(內容取自 CHANGELOG 那一段)。
- 分支合併後刪掉。

## 3. 版本號

單一來源是根目錄的 [`VERSION`](VERSION),遵循 [SemVer](https://semver.org/)。
`python tools/version.py --bump` 會同時改掉程式碼裡的三個常數(Bridge、worker、Python 客戶端)
並同步 `examples/`,不要手改。

| 改了什麼 | 怎麼 bump |
|---|---|
| 修 bug、修文件、補說明 | `patch` |
| 新功能、新端點、新設定、文件新章節 | `minor` |
| 呼叫端或部署者**不改就會壞**的變更(API、表結構、環境變數改名、行為改變) | 1.0 之前用 `minor` 並在 CHANGELOG 標「破壞性」;1.0 之後用 `major` |
| 只動 `.github/`、`spikes/`、各處的 `tests/` | 不用 bump(CI 會放行) |

**為什麼一定要 bump**:更新檢查只比對 `VERSION`。沒 bump 的變更合併後,已安裝的使用者**永遠不會收到**,
直到下一個有 bump 的版本。`version-bump` 這個 CI 檢查就是在擋這件事。

## 4. CHANGELOG 怎麼寫

格式照 [Keep a Changelog](https://keepachangelog.com/):`## [x.y.z] - YYYY-MM-DD`,底下分 Added／Changed／Fixed／Removed。

- **破壞性變更寫在該段落的最前面幾行**,而且要出現「破壞性」或「BREAKING」字樣。
  使用者機器上跑的是**舊版**的更新腳本,它只讀新版段落的**前 20 行**,並靠這兩個字判斷要不要特別警告。
- 寫「使用者會看到什麼差別」與「要做什麼」,不是寫改了哪個函式。
- 需要部署者動手的(補表、改環境變數、重新部署 Bridge、請使用者換 worker)單獨列一段「升級步驟」。

## 5. 不能出現在 repo 裡的東西

- **任何特定客戶、租戶、專案或人名**(含 commit 訊息)。範例一律用 `<your-tenant>`、`<your-bridge>`。
  CI 的 `lint-terms` 會擋;清單在 GitHub 的 repository variable `BANNED_TERMS`,本機放 `.banned-terms`(已 gitignore)。
- 金鑰、token、`.env`、`bridge.env`。
- `examples/` 裡客戶端副本的手改——一律改 `clients/` 正本再跑 `sync_clients.py`。

## 6. 在自己電腦上開發這個 repo

- **一律在分支上改**。更新腳本把「git 副本在 `main`／`master` 且版本不比遠端新」當成安裝,
  會強制同步;在分支上(或本地版本高於遠端)才會被當成開發副本略過。
- 想讓 agent 用你正在改的版本:把 skill 安裝目錄做成指向工作區的連結(Windows 用 junction),
  並確保工作區在分支上。
- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。
