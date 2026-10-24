# Mac 0.9.8 發布與小量公開 API 實測

2026-10-24 owner 明確授權合併、發布、原安裝上線及少量 token 的 LLM／Decisions 反應時間實測。範圍為 Mac source 0.9.8-mac.1、共用 cold Codex transport 與預設關閉的試驗工具；不啟用 warm pool、不開放後台控制項、不發布 Windows、不部署 Worker。原 profile、URL、device、KEY、模型與 64/64 容量保留。

## 發布前檢查

原 PR #42 的 Windows installer regression 在原生 Key 複製／讀回失敗；Win32 OpenClipboard(NULL) 後 EmptyClipboard 會失去有效 owner。修改為本程序同一執行緒的 message-only window，保留真前端點擊與 clipboard exact readback；新增成功、配置失敗、寫入失敗的所有權／清理回歸，沒有調低驗收。

依據：[Microsoft OpenClipboard 契約](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard)。完整 CI／Mac Release／下載安裝結果待本輪完成補入，不把未完成步驟列為通過。

## 公開 API 量測方法

`tools/benchmark_api_latency.py --apply --label after --rounds 3 --output /tmp/api-latency.json`：原安裝、臨時 RAM Key、原 HTTPS endpoint、每輪 Codex gpt-6.1-sol 與 Claude Haiku 4.5 各一筆 Chat 和一題 noul，合計 12 次序列推論；沒有 inference retry。檢查實際 model、Chat 固定短回答／noul 合法機率、成本和一題完整 receipt，結束撤銷測試 Key、核對原設定及所有既有 Key rows。

報告只有數字用量、model 名稱、格式／成本核對布林與固定分段耗時，無 body／答案／事件／stderr／token。三筆只報中位數與 max，不宣稱穩定 p95 或高併發吞吐；包含公開網路／Relay 往返。CLI 固定 system 開銷也算入實際 input tokens。

原型仍未通過完整 warm 启用門檻，#39 保持 open。此次 merge／release 不是 warm CLI 功能已預設啟用的證明。
