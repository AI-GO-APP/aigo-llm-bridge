# Windows 0.8.0 發布收據

本輪依使用者「Windows 已經完成，請合併發布 release」指示，合併 [PR #15](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/15) 並發布 [Windows 0.8.0 internal](https://github.com/AI-GO-APP/local-token-buffet-bridge/releases/tag/windows-installer-internal-v0.8.0)。**未升級或重啟 owner 正式 Windows 0.7.3，未執行 Mac release／Cloud 部署**。無 Authenticode 公發憑證，保持既有 internal prerelease 渠道；更新使用原 Ed25519 公鑰。

## 來源與閘門

- package commit：`0041259cb2595c41438a44490e6d9457a4547f60`；Windows 0.8.0、core `0.6.6-mac.2`、clean、redistributable=true、local_probe=false。
- 最終來源 PR CI：一般／Windows ZIP 通過；[原生驗收](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39886876865) 第一輪 WebView probe exit 2，前七項通過後退出，現有 artifact 未包含細分 stage，未判定根因；同一提交只重跑失敗 job 後通過。保留第一輪失敗，不將它改寫成成功。
- [正式 package／publish workflow](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/39887994161) 在 main 再執行回歸、原生 Setup A→B 及 AC-only power gate，成功後才 announce。
- 回歸 179 passed／2 skipped，原生電源 8/8、Setup A→B 48/48。後兩者使用拋棄 runner 與合成 profile；不代表正式機已升級或本人首次 OAuth 已完成。
- 真鎖定期間兩筆 Codex POST／PONG／cost 通過；完整解鎖後第四階段未完成，原因與原始 success=false 保留於 [鎖定 QA](2026-10-23-windows-locked.md)。首次新 OAuth／自有 Worker 乾淨部署仍另列未驗，使用者發布授權不是補做技術證據。

## 公開下載與更新政策

本機以既有 0.7.3 的 pinned public key、無 PAT 的 HTTPS 匿名下載全部六個 release assets，逐一核對大小／SHA256，另驗 artifacts／self-test、nupkg 內版本及三份引導文件、sleep-only 前端及無 installer profile。**12/12 項回讀檢查通過**；完整 metadata receipt 於 ignored `.desktop-build/windows080-release-readback/acceptance.json`。

| 欄位 | 結果 |
|---|---|
| policy sequence | 5；前版 4，持續遞增 |
| minimum_version | 0.7.0，保持可選更新，未提高強制更新門檻 |
| expires_at | 2026-11-22T02:14:51.780068+00:00 |
| public key fingerprint SHA256 前 16 碼 | `9682eb28e5ab9020`，與既有安裝相同 |
| 舊版 client check | installed=0.7.3、latest=0.8.0、available=true、required=false；使用隔離 policy cache，不變更正式服務 |

| 附件 | bytes | SHA256 |
|---|---:|---|
| AIGO.LLMBridge.Windows.Internal-0.8.0-windows-x64-internal-full.nupkg | 32895240 | `2fd2ed971994efce9e39566f62b11fa6582f837720ab9ea1cd9fa3c0f3570dc6` |
| AIGO.LLMBridge.Windows.Internal-windows-x64-internal-Portable.zip | 32894087 | `51b8d163b660ea8d1d35fe93b0d9bf48cca48cce4fed56af5fcfca71aef137e9` |
| AIGO.LLMBridge.Windows.Internal-windows-x64-internal-Setup.exe | 40409352 | `ad2f25df8b6c42dd445a0caef3d5a2739c0556cef984bb060e13aae285c52a35` |
| assets.windows-x64-internal.json | 320 | `7a3f5fcc8a1247fc907e7509499972277b4053ea05267dce12e5a208a9ee750f` |
| RELEASES-windows-x64-internal | 122 | `7cd70d314905343938dc4753b9922a76e4a918399ac6d93861c0de1359bf5861` |
| releases.windows-x64-internal.json | 317 | `1c0d3e3e4288fd2c0753e4d701ca2ef6812e1694907cd2ba84d01bf8941b2144` |

## 功能與範圍

新增五步 onboarding：插電自動休眠同意、官方訂閱 CLI 授權、Cloudflare OAuth／自有帳戶、一鍵或 AI IDE 協作 Worker 部署、長效 KEY 與真 HTTPS cost 交付。新 KEY 全來源預設；正常更新保留原 URL、KEY、裝置 profile、metadata 與完成旗標。

電源只改 AC sleep／hibernate／unattended sleep。螢幕、鎖定、DC、闔蓋／實體按鍵保留，無 HKCU 鎖定寫入；一般權限優先，電源 ACL 不足才選用 UAC。本輪未在 owner 工作站套用電源，亦未將 UI 閉窗當成服務停止。
