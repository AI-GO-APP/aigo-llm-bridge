/* Shared by the console and executable example acceptance checks. No credentials. */
"use strict";
const BridgeExamples = (() => {
  const ps = value => "'" + value.replace(/'/g, "''") + "'";
  const sh = value => "'" + value.replace(/'/g, "'\"'\"'") + "'";
  function build(base, model, format, operation = "chat") {
    const url = base.replace(/\/$/, "") + (operation === "models" ? "/models" : "/chat/completions");
    const body = JSON.stringify({model, messages:[{role:"user", content:"Reply exactly PONG."}], stream:false}, null, 2);
    if (format === "powershell") return `# 先將 API 金鑰存入目前終端的 LLM_BRIDGE_KEY 環境變數\nif (-not $env:LLM_BRIDGE_KEY) { throw '請先設定 LLM_BRIDGE_KEY' }\n$headers = @{ Authorization = "Bearer $env:LLM_BRIDGE_KEY" }\n${operation === "models" ? `Invoke-RestMethod -Uri ${ps(url)} -Headers $headers` : `$body = ${ps(body)}\n$result = Invoke-RestMethod -Uri ${ps(url)} -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))\n$result.choices[0].message.content`}`;
    if (format === "curl") return `# Bash / zsh：先設定 LLM_BRIDGE_KEY 環境變數\n: "\${LLM_BRIDGE_KEY:?請先設定 LLM_BRIDGE_KEY}"\ncurl --fail-with-body --max-time 100 ${sh(url)} \\\n  -H "Authorization: Bearer $LLM_BRIDGE_KEY"${operation === "models" ? "" : ` \\\n  -H 'Content-Type: application/json' \\\n  --data-raw ${sh(body)}`}`;
    return `# Python 3（先 python -m pip install certifi）；設定 LLM_BRIDGE_KEY 環境變數\nimport json\nimport os\nimport ssl\nimport certifi\nimport urllib.request\n\nheaders = {\n    "Authorization": "Bearer " + os.environ["LLM_BRIDGE_KEY"],\n    "Content-Type": "application/json",\n    "User-Agent": "aigo-llm-bridge-client/1.0",\n}\n${operation === "models" ? "" : `payload = json.loads(${JSON.stringify(body)})\n`}request = urllib.request.Request(\n    ${JSON.stringify(url)},\n    headers=headers,${operation === "models" ? "" : '\n    data=json.dumps(payload).encode("utf-8"),'}\n)\nwith urllib.request.urlopen(request, timeout=100, context=ssl.create_default_context(cafile=certifi.where())) as response:\n    result = json.load(response)\nprint(${operation === "models" ? 'json.dumps(result, ensure_ascii=False, indent=2)' : 'result["choices"][0]["message"]["content"]'})`;
  }
  return {build};
})();
if (typeof module !== "undefined") module.exports = BridgeExamples;
