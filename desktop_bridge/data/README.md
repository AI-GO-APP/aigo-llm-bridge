# Codex 純 Chat catalog 來源

`codex-chat-minimal-0163a11.json` 只供 `inference_profile.py` 已驗證的 Mac native CLI／gpt-6.1-sol 使用，不是模型探索目錄或訂閱 entitlement。沒有登入資料或 caller 內容。

- 上游 [openai/codex models.json](https://github.com/openai/codex/blob/5425d3e625daa58eea3ad1de27c087eb3b2ffbd3/codex-rs/models-manager/models.json)，tag `rust-v0.163.0-alpha.11`，commit `5425d3e625daa58eea3ad1de27c087eb3b2ffbd3`。
- 原始整份 catalog SHA256 `943ca7fe1d19ed019054158303f0dbbd80b3bef43b3aa425a71aa7cb3fb52c2b`。
- 只選取 slug=gpt-6.1-sol，完整保留其模型／能力／context／reasoning／方案 metadata；覆寫 tool_mode=direct、shell_type=disabled、apply_patch_tool_type=null、experimental_supported_tools=[]。
- model_messages 改為 `{"instructions_template":""}`，移除不使用的 agent 文案。每題另以 caller 原始 system／developer 內容設定 baseInstructions，空內容亦明確傳空字串，不回退上游 coding prompt。執行限制由 sandbox、never approval、工具設定、effective config 與事件拒絕獨立執行。
- 輸出以 UTF-8、ensure_ascii=false、indent=2、尾端換行；SHA256 `32682dd2713a20fc44149b00a40df78153d67760c6a73c0c4eb14eb9995bfe26`。
- 目前已驗 Mac CLI 0.163.0-alpha.11 的 binary SHA256 `8a6dc3938a2f5d30cc19c50b9ccad83a5aa2ca4a2e3411665430bb78a917220a`。其他 build／升級版本預先選 standard 並記原因；沒有自動下載或擴大名單。

上游授權與 notice 原文隨附 [Apache 2.0](CODEX-LICENSE.txt)、[NOTICE](CODEX-NOTICE.txt)。更新必須重驗 provenance、native wire、管理員設定、完整 caller 保留、同一容量帳本與真實用量；不在 runtime 下載未審查 catalog 或讀取 owner models cache 當發布資料。
