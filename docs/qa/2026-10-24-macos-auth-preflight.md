# Mac 0.9.15：冷Claude預檢重新驗證

2026-10-24，R-28／D-48，refs #39／#46。已合併、公開發布並完成原機更新測試，但64端到端驗收未過；原機已回復0.9.12、Worker0.9.5、4＋4／64／64。0.9.13結果交付與0.9.14預檢的所有失敗收據保留，不重送原推論。

## 證據與邊界

0.9.14的2筆Claude503在provider_setup約230ms，cli_spawn／inference為null。當時native status後續皆Ready；48次純metadata＋一筆另立合成PONG伴隨80次metadata，128/128為Ready且未見credential-metadata／settings／cli_state／binary stat改變。一筆獨立PONG為566 input／48 output、USD0.000806牌價等值，1次請求／無推論重送、測試Key撤銷。未重現失敗，不能宣稱已確認單一根因，也不要求使用者為未知問題重登入。

只在冷Claude、尚未建立推論Child前多做一次fresh status：第一判定負值或共享讀取中世代改變，丟棄舊判定、重新按當前世代查詢，需穩定Ready才繼續。第二次仍負值／不穩、取消／原期限或pacer後變動維持拒絕；Codex warm與已開始模型均不重跑。沒有讀取credential內容／登入／換帳號／改全域設定，推論函式／prompt／flags／schema／StructuredOutput不變。

## 驗收

專項驗證負值後Ready／讀取中世代變動後穩定各只spawn一次推論，持續負值／持續變動不spawn，取消在第二次前停止、Codex不重新驗證；原pacer後世代拒絕仍驗。本機Bridge366 passed／18平台限定skip，專項15 passed；原生Cocoa65張畫面、native clipboard、真save panel取消與儲存、CSV及關閉viewer服務仍在均通過。CI、公開ZIP／原機更新通過；新一輪兩provider×LLM／Decisions為4 serial＋3×16全正確，64波47/64，整輪99/116，詳下列失敗與回復收據。Meta重新驗證次數與CLI／完整usage分列，不以Ready當真推論證據。#39完整warm及真OpenRouter對照仍獨立。

首輪CI的一般檢查／Windows Desktop通過；Windows installer的schema reservation排序測試在背景執行緒進入前使用0.1秒wall deadline，遇runner排程後未進入assert事件（450 passed／14 skip／1 failed）。移除與排序無關的短期限，保留專屬deadline回歸，使用事件控制的有界等待；不變更正式排程／期限語義。後續CI以修正版head重新完整執行，保留首輪失敗。

## 發布、公開下載與原機更新

PR [#59](https://github.com/AI-GO-APP/local-token-buffet-bridge/pull/59) 最終head `04a5c1466a7db6b70bfbe8ad9c351c3c467842c3` 的一般CI40099520283、Windows Desktop40099520285、Windows installer40099520286、Mac40099520287全通過後合併，來源 `12758e75e73377bf73770e7ce1d418b57fb85717`。Mac [發布run40100033241](https://github.com/AI-GO-APP/local-token-buffet-bridge/actions/runs/40100033241) 成功；四附件匿名下載、clean manifest／commit／runtime比對通過，ZIP SHA256 `53e0422ee55b4092dfa036468219b528978feece99d1c859fed1c39ff1af47c9`。真公開ZIP安裝／互斥／停止、原profile更新與batch poll證據通過。本版未部署Worker或發布Windows，既有綁定Worker保持0.9.5-relay。

更新前後7份provider契約檔及9個native推論／command／usage／auth函式逐項相同。providers.py有metadata預檢修正，因此沒有把整檔宣稱未變；Decisions prompt／schema／thinking與CLI flags不變。

## 真公開API：保留完整失敗

沿用0.9.12／Worker0.9.4的既有116筆基準，不重跑paid baseline。本輪0.9.15／Worker0.9.5另做4 serial、3×16全正確才升64；原固定HTTPS、兩provider×Chat／Decisions平衡、相同合成payload指紋。兩臂不同臨時Key對，本次兩Key更新前後沿用。這是整組Relay／batch／預檢前後比較，不是單一變因隨機實驗。沒有對失敗UUID重送模型。

| 類型（serial各1筆） | 秒 | input／output tokens |
|---|---:|---:|
| codex chat | 10.1633 | 506／6 |
| codex decisions | 6.8938 | 2789／49 |
| claude chat | 3.9645 | 1061／118 |
| claude decisions | 9.3524 | 1546／841 |

Chat題文字以o200k_base估算500 caller tokens，不是實際OpenRouter帳單。Decisions另題，StructuredOutput原樣保留。

| 同步波次 | 正確 | p50／p95 秒（含失敗） | admission span 秒 | 本機Runtime p95 秒 |
|---|---:|---:|---:|---:|
| after_burst_16_round_1 | 16/16 | 7.1663／16.6835 | 4.7042 | 14.671 |
| after_burst_16_round_2 | 16/16 | 9.2359／23.4507 | 12.5266 | 16.898 |
| after_burst_16_round_3 | 16/16 | 8.7119／18.6294 | 5.4717 | 8.129 |
| after_burst_64_round_4 | 47/64 | 10.9589／102.3766 | 6.7899 | 7.944 |

64波：17筆外部連線例外（沒有HTTP成功狀態），其中9筆同UUID在本機已completed且完整usage／started=completed=1，8筆無本機收據；沒有收據不能證明未推論／零費用。不可只取47筆成功算成通過，也不能把本機Runtime的條件樣本p95當成完整端到端p95。

全116筆的DB核對：108筆本機收據完整、108 started／108 completed；已知input133,180／output16,868、USD0.2589352牌價等值，另8筆unknown。API成功回應可見之用量127,661／16,344、USD0.2475742只是子集，不是整輪用量。牌價等值不是訂閱實付或實際OpenRouter對照。Claude metadata rechecks=0，這輪沒有重現auth503，但沒有真實觸發重新查詢可作根因證明。

本機tree peak RSS6,911,712KiB，較舊基準2,431,856KiB約增加184.2%；FD10400超過8192採樣守門值，peak descendants61、running45、pool53。control health p95仍0.0021秒，不能據此宣稱網路／資源根因已排除。CPU431.9%是ps lifetime平均採樣最大值、100%=一core；FD亦為採樣估算。原guard僅在wave之間阻止繼續升級，不是執行中的OS硬限制，此處必須保留未達門檻。

結束前metadata（回復後counter重設，先保存）：

```json
{
  "relay_transport": {
    "poll_responses": 40,
    "batch_responses": 40,
    "legacy_responses": 0,
    "works_dispatched": 108,
    "peak_inflight": 50,
    "protocol_errors": 4,
    "duplicate_rejections": 0,
    "forward_errors": 1,
    "results_not_accepted": 2,
    "result_delivery_retries": 5,
    "inflight": 0,
    "forward_limit": 72,
    "batch_size": 8,
    "seen_entries": 0,
    "stopped": false,
    "poll": {
      "requests_started": 45,
      "requests_completed": 40,
      "requests_failed": 4,
      "connections_created": 4,
      "reused_requests": 37,
      "proxy_requests": 0,
      "idle_discarded": 0,
      "last_failure": {
        "category": "io",
        "phase": "headers",
        "status": null,
        "error_class": "RemoteDisconnected",
        "reused": true,
        "idle_ms": 9
      },
      "active": 1,
      "idle": 0,
      "limit": 1,
      "closed": false
    },
    "results": {
      "requests_started": 113,
      "requests_completed": 107,
      "requests_failed": 6,
      "connections_created": 25,
      "reused_requests": 84,
      "proxy_requests": 0,
      "idle_discarded": 19,
      "last_failure": {
        "category": "io",
        "phase": "headers",
        "status": null,
        "error_class": "RemoteDisconnected",
        "reused": true,
        "idle_ms": 9930
      },
      "active": 0,
      "idle": 1,
      "limit": 8,
      "closed": false
    },
    "local": {
      "requests_started": 108,
      "requests_completed": 108,
      "requests_failed": 0,
      "connections_created": 108,
      "reused_requests": 0,
      "proxy_requests": 0,
      "idle_discarded": 0,
      "last_failure": null,
      "active": 0,
      "idle": 0,
      "limit": 72,
      "closed": false
    }
  },
  "claude_metadata_rechecks": {
    "not_ready": 0,
    "generation_changed": 0
  }
}
```

## 零推論補查、已確認風險與下一步

回復後，完全相同公開host／TLS與呼叫端opener做3×64 health，192/192成功，各波max7.2582／7.5196／3.7815秒；零模型／零Key／無CLI。未重現連線失敗，不能當作實際推論壓力測試或證明先前純網路故障。

已確認Worker回poll即標dispatched，沒有收到Relay已收batch的確認；poll回應遺失後同session不再交付，存在工作遺失風險。8筆無本機收據與之相容，但不能斷言就是同一poll batch遺失。9筆本機完成但外部未收到也需獨立釐清。結構修復與零推論fault／真TLS／執行中資源門檻追蹤 [#60](https://github.com/AI-GO-APP/local-token-buffet-bridge/issues/60)，優先有界單批batch_id／session／ack、重複不再次接入，不以任意模型重試掩蓋。

## 正式狀態與資料保留

因64驗收未過，0.9.15 Release標prerelease／64-way acceptance failed，四附件bytes保留不覆寫；原機已正常排空回復0.9.12，installed core與該穩定版公開ZIP吻合。minimal4＋standard4／workers64／pending64，idle8、接受請求、running／queued／refill failures為0。73筆原Key rows全部保留，總75 rows、3把owner有效Key、本輪2把測試Key撤銷；全部設定／固定URL／profile／個人Codex設定保留。

#39完整100真pair／cold-warm3波64／RSS／Windows門檻與#46真OpenRouter同題仍未完成，兩issue保持開啟。0.9.13／14／15的失敗不得由後續成功覆蓋，也不回填unknown為零。原始request／response／credential不落磁碟；私有allowlist receipts在`.desktop-build/0915-auth-preflight`及原安裝`sources/macos-source-v0.9.15-mac.1`。本輪有發布與更新測試，沒有宣稱新版已正式放行。
