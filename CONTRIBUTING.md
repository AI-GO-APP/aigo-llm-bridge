# 參與開發與維護

這個 repo 是一個**公開、通用**的套件:Bridge、worker、呼叫端、範例 app 與文件。
流程只有一條:**分支 → PR → CI 全綠 → 合併**,不直接推 `main`。
本機怎麼跑 Bridge 與測試見 [docs/12](docs/12-local-development.md)。

## 1. 一次變更的完整流程

```bash
git switch main && git pull --ff-only
git switch -c fix/stream-timeout-message          # 分支前綴見下表

# … 改程式、文件 …

python tools/sync_clients.py                        # 改了 clients/ 才需要
python tools/version.py --bump patch                # 或 minor / major,見 §3
# 在 CHANGELOG.md 新的 [x.y.z] 段落寫下這一版的變更與升級影響(§4)

cd hosted && python -m pytest -q && cd ..
cd worker && python -m pytest tests -q && cd ..
python -m pytest tools/tests -q
python tools/version.py --check
python tools/scan_secrets.py
python tools/lint_terms.py --commits                # 本機有 .banned-terms 時才檢查得到

git push -u origin fix/stream-timeout-message
gh pr create --fill                                  # 會帶出 PR 範本
```

| 分支前綴 | 用途 | PR 標題範例 |
|---|---|---|
| `feat/` | 新功能、新文件章節 | `feat: 串流支援 tool calls(0.4.0)` |
| `fix/` | 修 bug、修錯的文件 | `fix: stream_timeout 事件漏帶 job_id(0.3.1)` |
| `docs/` | 只改文件措辭、不改行為 | `docs: 疑難排解補上 CSP 案例(0.3.1)` |
| `chore/` | CI、測試、spikes,**部署者與使用者拿不到的東西** | `chore: worker 測試加 macOS` |

PR 標題結尾帶上新版本號,合併後一眼就能對回 CHANGELOG 與 Release。

## 2. 合併規則

- **每個 PR 至少一位維護者看過**;自己開的 PR 可以自己合,但請在 PR 裡寫清楚測過什麼。
- CI 全綠才合併:`lint-terms`、`secrets`、`python-syntax`、`tests`、`hosted`、`worker`、`docs`、`version-bump`。
- 合併方式用 **Create a merge commit**,保留分支上的 commit,版本號對得回 PR。
- 合併後 `release` workflow 自動打 tag `vX.Y.Z`、建立 GitHub Release(內容取自 CHANGELOG 那一段),
  並附上 worker、開機自動啟動範本與三種客戶端檔案——docs/04 的下載網址靠的就是這些附件。
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

**為什麼一定要 bump**:每一次合併進 `main` 的變更都要對得回一個 tag 與 Release。部署者靠 Release 決定要不要升級、
靠 `/healthz` 的 `version` 知道線上跑的是哪一版;沒 bump 的變更混在上一版裡,兩件事都會對不上。
`version-bump` 這個 CI 檢查就是在擋這件事。

## 4. CHANGELOG 怎麼寫

格式照 [Keep a Changelog](https://keepachangelog.com/):`## [x.y.z] - YYYY-MM-DD`,開頭一兩句摘要,
接著**固定一段「升級影響」**,再分 Added／Changed／Fixed／Removed。

```markdown
## [0.4.0] - 2026-10-15

一兩句:使用者會看到什麼差別。

### 升級影響
- Bridge:需要重新部署／不需要
- 表:執行 `provision_tables.py --apply` 補欄位／不需要
- 環境變數:新增 `XXX`(選填)／不需要
- worker:建議更新／不需要
- 客戶端:`bridge.ts` 需要重新複製／不需要
```

- **破壞性變更寫在段落最前面**,並含「破壞性」字樣。
- 寫「使用者會看到什麼差別」與「要做什麼」,不是寫改了哪個函式。
- 能不能退版:`provision_tables.py` 只新增、不刪欄;若某一版改了既有欄位的意思或格式,在升級影響寫明「不能退回 x.y.z」。

## 5. 不能出現在 repo 裡的東西

完整清單與原因見 [docs/11](docs/11-security.md)。重點:

- **任何金鑰、token、密碼**,以及 `*.env`、`worker.json`、`.banned-terms` 這類檔案。CI 的 `secrets`
  (`tools/scan_secrets.py --history`)會擋,連 commit 歷史一起查。**進過 commit 就當成已外洩**,先換金鑰再移除。
- **任何特定客戶、租戶、專案或人名**(含 commit 訊息與**作者名**)。範例一律用 `<your-tenant>`、`<your-bridge>`。
  CI 的 `lint-terms` 會擋;清單在 GitHub 的 repository **secret** `BANNED_TERMS`(不能用 variable:會以明文印在
  公開的 CI 紀錄裡),本機放 `.banned-terms`(已 gitignore)。
- git 作者名會進公開紀錄:在這個 repo 設定不含公司或客戶名稱的作者,例如
  `git config user.name <你的名字>`、`git config user.email <GitHub noreply 信箱>`。
- `examples/` 裡客戶端副本的手改——一律改 `clients/` 正本再跑 `sync_clients.py`。

## 6. 風格

- 文件與註解以繁體中文為主,API 名稱與程式碼識別字用英文。
- 文件講「讀者要做什麼、做完怎麼確認」;實測數字寫進 docs/01,並附量法。
- 文件裡的相對連結都要指到存在的檔案(CI 的 `docs` 會檢查)。
