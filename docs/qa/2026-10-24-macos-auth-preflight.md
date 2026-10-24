# Mac 0.9.15：冷Claude預檢重新驗證

2026-10-24，R-28／D-48，refs #39／#46。候選尚未合併／發布／正式安裝；原機已回復0.9.12、Worker0.9.5、4＋4／64／64。0.9.13結果交付與0.9.14預檢的所有失敗收據保留，不重送原推論。

## 證據與邊界

0.9.14的2筆Claude503在provider_setup約230ms，cli_spawn／inference為null。當時native status後續皆Ready；48次純metadata＋一筆另立合成PONG伴隨80次metadata，128/128為Ready且未見credential-metadata／settings／cli_state／binary stat改變。一筆獨立PONG為566 input／48 output、USD0.000806牌價等值，1次請求／無推論重送、測試Key撤銷。未重現失敗，不能宣稱已確認單一根因，也不要求使用者為未知問題重登入。

只在冷Claude、尚未建立推論Child前多做一次fresh status：第一判定負值或共享讀取中世代改變，丟棄舊判定、重新按當前世代查詢，需穩定Ready才繼續。第二次仍負值／不穩、取消／原期限或pacer後變動維持拒絕；Codex warm與已開始模型均不重跑。沒有讀取credential內容／登入／換帳號／改全域設定，推論函式／prompt／flags／schema／StructuredOutput不變。

## 驗收

專項驗證負值後Ready／讀取中世代變動後穩定各只spawn一次推論，持續負值／持續變動不spawn，取消在第二次前停止、Codex不重新驗證；原pacer後世代拒絕仍驗。本機Bridge366 passed／18平台限定skip，專項15 passed；原生Cocoa65張畫面、native clipboard、真save panel取消與儲存、CSV及關閉viewer服務仍在均通過。CI、公開ZIP／原機更新及新一輪兩provider×LLM／Decisions、3×16通過才64的結果待逐項補證。Meta重新驗證次數與CLI／完整usage分列，不以Ready當真推論證據。#39完整warm及真OpenRouter對照仍獨立。

首輪CI的一般檢查／Windows Desktop通過；Windows installer的schema reservation排序測試在背景執行緒進入前使用0.1秒wall deadline，遇runner排程後未進入assert事件（450 passed／14 skip／1 failed）。移除與排序無關的短期限，保留專屬deadline回歸，使用事件控制的有界等待；不變更正式排程／期限語義。後續CI以修正版head重新完整執行，保留首輪失敗。
