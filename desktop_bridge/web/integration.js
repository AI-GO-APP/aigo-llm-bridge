/* Shared by the console and executable example acceptance checks. No credentials. */
"use strict";
const BridgeExamples = (() => {
  const ps = value => "'" + value.replace(/'/g, "''") + "'";
  const sh = value => "'" + value.replace(/'/g, "'\"'\"'") + "'";
  function build(base, model, format, operation = "chat") {
    const root = base.replace(/\/(?:api\/)?v1\/?$/, "").replace(/\/$/, "");
    const paths = {models:"/models", chat:"/chat/completions", capabilities:"/bridge/v1/model-capabilities", refresh:"/bridge/v1/models/refresh", probe:"/bridge/v1/models/probe", decisions:"/api/alpha/decisions"};
    if (!Object.hasOwn(paths, operation)) throw new Error("Unknown operation");
    const isGet = ["models", "capabilities"].includes(operation);
    const url = (["models", "chat"].includes(operation) ? base.replace(/\/$/, "") : root) + paths[operation];
    const decision = {model, state:"A synthetic customer asks for a quotation.", questions:{needs_response:{type:"noul", instructions:"Does the customer need a response?"}}, provider:{data_collection:"deny"}};
    const payload = operation === "decisions" ? decision : operation === "refresh" ? {} : operation === "probe" ? {model, protocol:"decisions"} : {model, messages:[{role:"user", content:"Reply exactly PONG."}], stream:false};
    const body = JSON.stringify(payload, null, 2);
    if (format === "powershell") return `# 先將 API 金鑰存入目前終端的 LLM_BRIDGE_KEY 環境變數\nif (-not $env:LLM_BRIDGE_KEY) { throw '請先設定 LLM_BRIDGE_KEY' }\n$headers = @{ Authorization = "Bearer $env:LLM_BRIDGE_KEY" }\n${isGet ? `Invoke-RestMethod -Uri ${ps(url)} -Headers $headers` : `$body = ${ps(body)}\n$result = Invoke-RestMethod -Uri ${ps(url)} -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))\n${["decisions","probe"].includes(operation) ? "$result.answers" : operation === "refresh" ? "$result" : "$result.choices[0].message.content"}`}`;
    if (format === "curl") return `# Bash / zsh：先設定 LLM_BRIDGE_KEY 環境變數\n: "\${LLM_BRIDGE_KEY:?請先設定 LLM_BRIDGE_KEY}"\ncurl --fail-with-body --max-time 100 ${sh(url)} \\\n  -H "Authorization: Bearer $LLM_BRIDGE_KEY"${isGet ? "" : ` \\\n  -H 'Content-Type: application/json' \\\n  --data-raw ${sh(body)}`}`;
    return `# Python 3（先 python -m pip install certifi）；設定 LLM_BRIDGE_KEY 環境變數\nimport json\nimport os\nimport ssl\nimport certifi\nimport urllib.request\n\nheaders = {\n    "Authorization": "Bearer " + os.environ["LLM_BRIDGE_KEY"],\n    "Content-Type": "application/json",\n    "User-Agent": "aigo-llm-bridge-client/1.0",\n}\n${isGet ? "" : `payload = json.loads(${JSON.stringify(body)})\n`}request = urllib.request.Request(\n    ${JSON.stringify(url)},\n    headers=headers,${isGet ? "" : '\n    data=json.dumps(payload).encode("utf-8"),'}\n)\nwith urllib.request.urlopen(request, timeout=100, context=ssl.create_default_context(cafile=certifi.where())) as response:\n    result = json.load(response)\nprint(${isGet ? 'json.dumps(result, ensure_ascii=False, indent=2)' : ["decisions","probe"].includes(operation) ? 'result["answers"]' : operation === "refresh" ? 'json.dumps(result, ensure_ascii=False, indent=2)' : 'result["choices"][0]["message"]["content"]'})`;
  }
  return {build};
})();
if (typeof module !== "undefined") module.exports = BridgeExamples;
