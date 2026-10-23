# Windows 0.8.1 安全修補驗收

狀態：0.8.1 已宣布、原生安裝已升級，真實 HTTPS 呼叫通過；正式常駐重啟尚未放行，原因見下方。core 0.6.7 只識別本次共用修補，無 Mac release／Cloud 部署。

## 範圍與已完成來源檢查

修補當日安全盤點的 P0／P1：CA／Windows runtime、Relay redirect／回應上限、Claude stdin、schema 子程序預算、Worker queue reservation、Wrangler／Node 基線、hash-lock 與 CI 漏洞閘門。邊界與契約見 [SECURITY](../SECURITY.md)。

- 隔離 Python 3.14.9／OpenSSL 3.5.9／certifi 2026.10.19；未替換全球 Python／Node，也未更動供應商登入。
- Windows／core 回歸目前 186 passed、2 skipped；Worker／平台 adapter 10 passed。
- 精確鎖檔 OSV 120 筆查詢零命中；npm audit 零命中。零命中不等於無未知／native 漏洞。
- 實際既有 HTTPS health 以產品 User-Agent 回 200 且 device_online=true。歷史 Python 預設 User-Agent 的 403 不足以判斷離線。
- 測試僅合成內容，不提交完整 KEY、正式 endpoint、account ID 或原始 I/O。
- 本機最終 native A→B 採 `--skip-renderer`，避免變更使用中的剪貼簿／桌面；首次候選 33／33（最終重建驗證中），CI 預設仍完整 renderer。
- 真實 source r2 共 7／7：Codex text、Codex／Claude schema、兩來源工具提案、兩來源檔案 canary。URL／device／KEY 重開保留、原文／完整 KEY 磁碟掃描、argv、成本回執共 9／9。每筆成本以當次用量、牌價與 receipt 交叉核對，不要求不同請求／cache 狀態回相同金額。
- source r1 的 Claude 工具提案因完整 JSON code fence 回 502；修補只去完整外框後嚴格驗證，不重送既有工作。該失敗仍有 token／成本 metadata。另一次直接 CLI 格式診斷未走 Bridge 計量，只保留 shape；不得把有收據案例的成本加總說成涵蓋所有診斷。
- 工具回歸 52 passed（Windows 明確使用 Git Bash，避免誤叫 System32 WSL shim）；文件／terms／歷史 secrets 掃描通過。

## 已完成原生與公開發布閘門

- frozen 真實 7／7，URL／KEY／metadata／成本等 8 項檢查通過；跨程序 controller spy 無法觀察 frozen argv，因此未計入該項。
- 本機真 Setup→A→B 33／33，略過 renderer 以保留使用者剪貼簿；GitHub runner 完整 native 49／49、隔離電源 8／8。[main 原生](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39896163566)。
- [PR18](https://github.com/AI-GO-APP/aigo-llm-bridge/pull/18)、[PR19](https://github.com/AI-GO-APP/aigo-llm-bridge/pull/19) 已合併。最終來源 e6e2d1e7c3cba086cec921fa7d580fa1e43ee49e；[publish](https://github.com/AI-GO-APP/aigo-llm-bridge/actions/runs/39896167853) 成功，[0.8.1 release](https://github.com/AI-GO-APP/aigo-llm-bridge/releases/tag/windows-installer-internal-v0.8.1) 公開。
- 匿名 HTTPS assets／原公鑰 policy 回讀 16／16；sequence 6、minimum 0.7.0、公鑰 fingerprint 9682eb28e5ab9020。實際包含 Python 3.14.9／OpenSSL 3.5.9／certifi 2026.10.19，無 Authenticode。
- 正式原生 0.7.3→0.8.1 成功；Codex text／schema、Claude schema／tools 四次真 HTTPS 通過，usage.cost 與 OpenRouter 牌價、實際 token、receipt 核對一致。正式 Claude argv 共 13 次樣本無 caller marker／schema flag。
- 原 29 個 key row、7 個設定、183 筆完成 log 保留。第一次 row hash 比對因 baseline 23 欄、現行 28 欄誤判，保留失敗收據；以升級前備份證明五個 nullable 欄早已存在，再投影原 23 欄及比對完整 28 欄，183／183 未改。未以修改正式資料來通過測試。

## 正式常駐尚未完成的原因

首次 native 重啟前的 drain 無法聯繫 owner，流程未實際重啟；後續一次真 HTTPS Codex 成功不算重啟證據。檢查發現另一個流程新安裝並啟動 source 格式 core 0.7.1，接管 8920 與同一 profile。這與原生安裝器 0.8.1 屬不同版本系列，不能直接比較新舊；未停止該程序，已向使用者確認是否仍有其他部署進行。0.8.1 安裝檔仍完整。測試 KEY 暫留受保護測試檔，待受控重啟驗證後撤銷。

另以自有隔離 socket 證明 Windows SO_REUSEADDR 允許同址雙 listener；新增 0.8.2 Windows-only 修補與驗收，見 [0.8.2 QA](2026-10-23-windows-082-security.md)。

後續來源 Session 明確交接並停止修改服務，已受控升級到 0.8.2，完成重啟後 HTTPS 及原資料／KEY 保留；測試 KEY 已撤銷、受保護檔已刪。上述 0.8.1 未完成重啟的歷史收據保留，不改寫成當時已成功。

Worker 修補只交付範本，不代表既有雲端已修補；未部署、未重配 DEVICE_KEY。Mac 與 Cloud 團隊工作不在本次範圍。

## 宣布前的封裝流程修復

首次 publish run 39894565618 的 package／native gates 成功，announce 在讀 artifacts.json 前失敗：將稽核檔與 installer 檔一起上傳使 artifact 共同根目錄提高一層。尚未建立 Windows 0.8.1 release 或變更 policy，正式仍為 0.7.3。修復將 dependency audit 分成獨立 artifact，加入跨 job common-root 回歸；不換 signer、不覆寫已發布版本，也不盲目重跑舊失敗 job。

PR #19 首次 native run 39895161883 在 APPLY B 的子 CLI 回 exit 1；先前 source／renderer／最低版本等檢查成功。舊工具只記 exit code，未留下已去敏錯誤；新增只允許來源 literal UpdateError 的診斷後重新驗證，不能把缺少原因的失敗直接當成通過。
