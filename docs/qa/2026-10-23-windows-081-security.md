# Windows 0.8.1 安全修補驗收

狀態：候選驗收中；未宣布、未升級正式 Windows。core 0.6.7 只識別本次共用修補，無 Mac release／Cloud 部署。

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
- 工具回歸 51 passed（Windows 明確使用 Git Bash，避免誤叫 System32 WSL shim）；文件／terms／歷史 secrets 掃描通過。

## 待完成放行閘門

- 封裝後 schema helper、真正 Setup／A→B、原 URL／KEY／device／metadata／DPAPI 保留。
- 真實 Codex／Claude 訂閱呼叫、structured output、成本公式及中繼資料掃描。
- PR／CI／main／signed policy／公開附件匿名回讀。
- 正式 Windows 安全升級與重啟後真 HTTPS，原有資料及 key digest 比對。

Worker 修補只交付範本，不代表既有雲端已修補；未部署、未重配 DEVICE_KEY。Mac 與 Cloud 團隊工作不在本次範圍。

## 宣布前的封裝流程修復

首次 publish run 39894565618 的 package／native gates 成功，announce 在讀 artifacts.json 前失敗：將稽核檔與 installer 檔一起上傳使 artifact 共同根目錄提高一層。尚未建立 Windows 0.8.1 release 或變更 policy，正式仍為 0.7.3。修復將 dependency audit 分成獨立 artifact，加入跨 job common-root 回歸；不換 signer、不覆寫已發布版本，也不盲目重跑舊失敗 job。
