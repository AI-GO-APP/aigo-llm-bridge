"use strict";
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("session")) {
  sessionStorage.setItem("bridge-session", fragment.get("session"));
  history.replaceState(null, "", location.pathname);
}
const token = sessionStorage.getItem("bridge-session") || "";
let state, page = "overview", initialized = false, polling = false, toastTimer, stopped = false, logGeneration = 0;
const names = {overview:"總覽", integration:"串接指南", keys:"API 金鑰", logs:"請求紀錄", models:"模型管理", settings:"連線與設定"};
const statuses = {queued:"排隊中", running:"執行中", completed:"已完成", failed:"失敗", rejected:"已拒絕", cancelled:"已取消", interrupted:"已中斷"};
const date = value => value ? new Date(value * 1000).toLocaleString("zh-TW", {month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hour12:false}) : "—";
function toast(text) { $("toast").textContent = text; $("toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $("toast").hidden = true, 4000); }
async function api(path, data, raw = false, timeout = 15000) {
  const response = await fetch(path, {method: data === undefined ? "GET" : "POST", cache:"no-store", headers:{Authorization:`Bearer ${token}`, ...(data === undefined ? {} : {"Content-Type":"application/json"})}, body:data === undefined ? undefined : JSON.stringify(data), signal:AbortSignal.timeout(timeout)});
  if (!response.ok) { const error = await response.json(); throw new Error(error.error || "操作未完成，請稍後再試。"); }
  return raw ? response.blob() : response.json();
}
async function run(button, work) {
  if (button?.disabled) return;
  if (button) button.disabled = true;
  try { await work(); } catch (error) { toast(error.message || "無法連線至 Bridge。"); }
  finally { if (button) button.disabled = false; }
}
async function copy(text) { try { await window.BridgePlatform.copyText(text); toast("已複製到剪貼簿"); } catch { toast("無法複製，請選取內容後手動複製。"); } }
function navigate(next) {
  if (!names[next]) next = "overview";
  page = next;
  if (next !== "integration") $("test-api-key").value = "";
  document.querySelectorAll(".page").forEach(el => el.hidden = el.id !== `page-${next}`);
  document.querySelectorAll("[data-page]").forEach(el => { el.classList.toggle("active", el.dataset.page === next); if (el.dataset.page === next) el.setAttribute("aria-current", "page"); else el.removeAttribute("aria-current"); });
  $("crumb").textContent = names[next]; document.title = `${names[next]} · LLM Bridge`;
  history.replaceState(null, "", `#${next}`);
  if (next === "logs") refreshLogs().catch(error => toast(error.message));
}
document.querySelectorAll("[data-page]").forEach(el => el.addEventListener("click", () => navigate(el.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(el => el.addEventListener("click", () => navigate(el.dataset.goto)));
document.querySelector(".brand").addEventListener("click", e => { e.preventDefault(); navigate("overview"); });
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
function badge(text, kind = "") { return `<span class="badge ${kind}">${esc(text)}</span>`; }
function statusBadge(status) { return badge(statuses[status] || status, status === "completed" ? "" : ["running","queued"].includes(status) ? "warning" : ["failed","rejected"].includes(status) ? "error" : "neutral"); }
function empty(title, text, action = "") { return `<div class="empty"><span class="empty-icon"><svg><use href="#i-pulse"/></svg></span><h3>${esc(title)}</h3><p>${esc(text)}</p>${action}</div>`; }
function logTable(rows, full = false) {
  if (!rows.length) return empty(full ? "沒有符合條件的請求" : "準備好迎接第一個請求", full ? "試著切換篩選條件，或在服務發出請求後回來查看。" : "建立 API 金鑰，將你的服務連接到 Bridge。", full ? "" : '<button class="secondary compact" id="empty-connect">開始接入 →</button>');
  return `<table><thead><tr><th>模型 / 來源</th><th>狀態</th><th>耗時</th>${full ? "<th>HTTP</th><th>輸入 / 輸出 tokens</th><th>牌價估值 USD</th><th>錯誤分類</th>" : ""}<th>時間</th></tr></thead><tbody>${rows.map(row => `<tr><td class="model">${esc(row.model || "未指定模型")}</td><td>${statusBadge(row.status)}</td><td>${row.duration_ms == null ? "—" : `${(row.duration_ms / 1000).toFixed(2)} s`}</td>${full ? `<td>${esc(row.http_status ?? "—")}</td><td>${esc(row.prompt_tokens ?? 0)} / ${esc(row.completion_tokens ?? 0)}</td><td class="numeric">${row.cost_usd == null ? "—" : esc(Number(row.cost_usd).toFixed(6))}</td><td>${esc(row.error_code || "—")}</td>` : ""}<td>${date(row.created_ts)}</td></tr>`).join("")}</tbody></table>`;
}
const htmlCache = new Map();
function updateHTML(id, html) { if (htmlCache.get(id) !== html) { $(id).innerHTML = html; htmlCache.set(id, html); } }
function render() {
  $("preview-notice").hidden = !state.preview;
  const c = state.counts, keys = state.keys.filter(k => !k.revoked_ts), active = (c.queued || 0) + (c.running || 0);
  $("version").textContent = state.windows_release ? `Windows ${state.windows_release.version}` : `核心 ${state.version}`;
  $("service-badge").className = `badge ${state.accepting ? "" : "warning"}`;
  $("service-badge").innerHTML = `<i></i>${state.accepting ? "接受請求中" : "已暫停接單"}`;
  $("metric-keys").textContent = keys.length; $("nav-key-count").textContent = keys.length;
  $("metric-active").textContent = active; $("queue-detail").textContent = `${c.queued || 0} 筆排隊 · ${c.running || 0} 筆執行中`;
  $("metric-completed").textContent = c.completed || 0;
  $("metric-providers").textContent = Object.keys(state.auth).length ? Object.values(state.auth).filter(p => p.ready).length : "—";
  $("endpoint").value = state.endpoint;
  $("endpoint-kind").textContent = state.settings.public_url ? "HTTPS 入口" : "本機入口";
  $("path-transport").textContent = state.settings.public_url ? "HTTPS 轉接" : "本機連線";
  const transport = state.settings.relay_enabled ? `雲端轉接：${state.relay}` : state.settings.tunnel_name ? `Tunnel：${state.tunnel}` : state.settings.public_url ? "已設定網址 · 尚未啟用連線方式" : "僅限本機 · 尚未設定公開入口";
  $("transport-state").textContent = transport;
  for (const provider of ["claude","codex"]) {
    const auth = state.auth[provider], el = $(`${provider}-status`);
    el.className = `badge ${auth?.ready ? "" : auth ? "warning" : "neutral"}`;
    el.textContent = auth ? auth.ready ? "已登入" : "未就緒" : "檢查中";
  }
  $("refresh-auth").textContent = state.auth_checking ? "檢查中…" : "重新檢查 ↻";
  $("refresh-auth").disabled = state.auth_checking;
  $("pause").textContent = state.accepting ? "暫停接單" : "恢復接單";
  $("runtime-note").textContent = `${state.accepting ? "本機服務接受請求中" : "已暫停接受新請求"} · 連接埠 ${state.local_port}`;
  updateHTML("recent-logs", logTable(state.logs));
  $("key-total").textContent = `${keys.length} 把有效 / 共 ${state.keys.length} 把`;
  updateHTML("keys-list", state.keys.length ? `<table><thead><tr><th>名稱</th><th>金鑰</th><th>來源</th><th>每分鐘上限</th><th>狀態</th><th>建立時間</th><th>操作</th></tr></thead><tbody>${state.keys.map(k => `<tr><td>${esc(k.label)}</td><td class="model">${esc(k.prefix)}…</td><td>${esc(JSON.parse(k.providers).join(" / "))}</td><td>${k.rpm}</td><td>${badge(k.revoked_ts ? "已撤銷" : "有效", k.revoked_ts ? "neutral" : "")}</td><td>${date(k.created_ts)}</td><td><div class="row-actions">${k.revoked_ts ? "—" : `<button class="text-button" data-key-action="rotate" data-key="${esc(k.id)}">輪替</button><button class="text-button danger" data-key-action="revoke" data-key="${esc(k.id)}">撤銷</button>`}</div></td></tr>`).join("")}</tbody></table>` : empty("尚未建立 API 金鑰", "為你的第一個服務建立專屬金鑰，設定可用來源與請求上限。", '<button class="primary compact" id="empty-create">＋ 建立金鑰</button>'));
  $("relay-detail").textContent = state.relay; $("tunnel-detail").textContent = state.tunnel;
  renderIntegration();
  if (!initialized) { fillSettings(); renderModels(); initialized = true; }
}
async function refresh() {
  if (polling || stopped) return;
  polling = true;
  try {
    state = await api("/manage/state"); render(); $("connection-error").hidden = true;
    $("sync-label").textContent = `已更新 ${new Date().toLocaleTimeString("zh-TW", {hour12:false})}`;
    if (page === "logs") await refreshLogs();
  } catch (error) {
    $("connection-error").hidden = false;
    $("connection-error").textContent = error.message?.includes("管理連線") ? error.message : "無法連線至本機 Bridge。顯示的是上次取得的資料；請確認程式正在執行，或從捷徑重新開啟。";
    $("service-badge").className = "badge warning"; $("service-badge").textContent = "管理台離線";
    $("sync-label").textContent = "更新中斷";
  } finally { polling = false; }
}
function logQuery() { return new URLSearchParams({status:$("log-status").value, provider:$("log-provider").value}); }
async function refreshLogs() { const generation = ++logGeneration; const result = await api(`/manage/logs?${logQuery()}`); if (generation === logGeneration) updateHTML("all-logs", logTable(result.logs, true)); }
function modal(title, html) { $("modal-title").textContent = title; $("modal-body").innerHTML = html; if (!$("modal").open) $("modal").showModal(); }
function closeModal() { $("modal").close(); $("modal-body").replaceChildren(); }
$("close-modal").addEventListener("click", closeModal);
$("modal").addEventListener("close", () => $("modal-body").replaceChildren());
function confirmation(title, description, label, action) {
  modal(title, `<p class="dialog-note">${esc(description)}</p><div class="modal-actions"><button id="confirm-cancel" class="secondary">取消</button><button id="confirm-action" class="primary danger">${esc(label)}</button></div><p id="modal-error" class="inline-error" role="alert"></p>`);
  $("confirm-cancel").addEventListener("click", closeModal);
  $("confirm-action").addEventListener("click", () => modalRun($("confirm-action"), action));
}
async function modalRun(button, action) { button.disabled = true; try { await action(); } catch (error) { if ($("modal-error")) $("modal-error").textContent = error.message; else toast(error.message); } finally { button.disabled = false; } }
function showToken(value, allowed = ['claude','codex']) {
  modal("金鑰已建立", '<p class="dialog-note">完整金鑰只顯示這一次。請保存到呼叫服務的 secret 設定，關閉後無法再次查看。</p><input id="new-token" class="secret-input" readonly aria-label="新 API 金鑰"><div class="modal-actions"><button id="copy-token" class="secondary">複製金鑰</button><button id="token-done" class="primary">已保存，關閉</button></div>');
  $("new-token").value = value; $("copy-token").addEventListener("click", () => copy($("new-token").value)); $("token-done").addEventListener("click", closeModal);
  const button=document.createElement('button');button.className='secondary';button.textContent='複製給 AI IDE（含金鑰）';
  button.addEventListener('click',()=>run(button,async()=>{
    const model=state.settings.models.find(m=>m.provider==='codex' && allowed.includes(m.provider)) || state.settings.models.find(m=>allowed.includes(m.provider));
    if (!model) throw new Error('請先設定此金鑰可用的模型。');
    const info=await api('/manage/handoff?model='+encodeURIComponent(model.id));
    await copy(info.prompt.replace('LLM_BRIDGE_KEY 由擁有者另行提供；放入執行環境的 secret 設定。','LLM_BRIDGE_KEY='+$("new-token").value));
  }));
  $("copy-token").after(button);
}
function createKey() {
  modal("建立 API 金鑰", '<form id="key-form" class="modal-form"><p>用服務名稱識別金鑰，例如「內部客服」或「開發環境」。</p><label>服務名稱<input name="label" maxlength="60" required placeholder="輸入服務名稱" autofocus></label><fieldset><legend>允許的模型來源</legend><label class="check-label"><input name="claude" type="checkbox" checked> Claude</label><label class="check-label"><input name="codex" type="checkbox" checked> Codex</label></fieldset><label>每分鐘請求上限<input name="rpm" type="number" min="1" max="600" value="30" required><small>全機同時執行一筆推論，其他請求進入佇列。</small></label><p id="modal-error" class="inline-error" role="alert"></p><button class="primary" type="submit">建立金鑰</button></form>');
  $("key-form").addEventListener("submit", e => { e.preventDefault(); const f = e.target; modalRun(f.querySelector("button"), async () => { const selected = ["claude","codex"].filter(p => f.elements[p].checked); if (!selected.length) throw new Error("請至少選取一個模型來源。"); const result = await api("/manage/keys/create", {label:f.elements.label.value, providers:selected, rpm:Number(f.elements.rpm.value)}); showToken(result.token,selected); await refresh(); }); });
}
$("create-key").addEventListener("click", createKey);
$("keys-list").addEventListener("click", e => {
  if (e.target.closest("#empty-create")) return createKey();
  const button = e.target.closest("[data-key-action]"); if (!button) return;
  const key = state.keys.find(k => k.id === button.dataset.key), rotate = button.dataset.keyAction === "rotate";
  confirmation(rotate ? "輪替 API 金鑰" : "撤銷 API 金鑰", `「${key.label}」的舊金鑰將立即失效，排隊與執行中的工作也會取消。${rotate ? "請同步更新呼叫服務的新金鑰。" : "此操作無法復原。"}`, rotate ? "確認輪替" : "確認撤銷", async () => { const result = await api(`/manage/keys/${rotate ? "rotate" : "revoke"}`, {id:key.id}); if (rotate) showToken(result.token,JSON.parse(key.providers)); else { closeModal(); toast("金鑰已撤銷"); } await refresh(); });
});
function guide() { navigate("integration"); }
function renderIntegration() {
  $("integration-endpoint").value = state.endpoint;
  $("integration-transport").textContent = $("transport-state").textContent;
  const models = state.settings.models;
  updateHTML("integration-models", models.length ? models.map(m => `<div class="integration-model"><div><strong>${esc(m.provider === "claude" ? "Claude" : "Codex")}</strong><code>${esc(m.id)}</code></div>${badge(state.auth[m.provider]?.ready ? "CLI 已登入" : "CLI 未就緒", state.auth[m.provider]?.ready ? "" : "warning")}<button class="secondary compact" data-copy-model="${esc(m.id)}">複製模型 ID</button></div>`).join("") : empty("尚未設定模型", "請先到模型管理登錄模型。"));
  const selected = $("example-model").value;
  updateHTML("example-model", models.map(m => `<option value="${esc(m.id)}">${esc(m.id)}</option>`).join(""));
  if (models.some(m => m.id === selected)) $("example-model").value = selected;
  else if(models.some(m=>m.provider==='codex')) $("example-model").value=models.find(m=>m.provider==='codex').id;
  renderTestModels();
  renderExample();
}
function renderExample() {
  if (!state) return;
  const missing = !$("example-model").value && ["chat", "decisions", "probe"].includes($("example-operation").value);
  $("copy-example").disabled = missing;
  $("example-code").textContent = missing ? "請先登錄模型。" : BridgeExamples.build(state.endpoint, $("example-model").value, $("example-format").value, $("example-operation").value);
  $("example-model").disabled = !["chat", "decisions", "probe"].includes($("example-operation").value);
}
for (const id of ["example-model", "example-format", "example-operation"]) $(id).addEventListener("change", renderExample);
$("copy-example").addEventListener("click", () => copy($("example-code").textContent));
$("copy-integration-endpoint").addEventListener("click", () => copy($("integration-endpoint").value));
$("integration-models").addEventListener("click", e => { const button = e.target.closest("[data-copy-model]"); if (button) copy(button.dataset.copyModel); });
$("copy-integration").addEventListener("click", e => run(e.currentTarget,async () => {
  if (!state) return toast("請等待管理台連線。");
  const info=await api('/manage/handoff'+($("example-model").value ? '?model='+encodeURIComponent($("example-model").value) : ''));
  await copy(info.prompt);
}));
let testingConnection = false;
function renderTestModels() {
  if (testingConnection) return;
  for (const provider of ["claude", "codex"]) {
    const id = `test-model-${provider}`, models = state.settings.models.filter(m => m.provider === provider), selected = $(id).value;
    updateHTML(id, models.length ? models.map(m => `<option value="${esc(m.id)}">${esc(m.id)}</option>`).join("") : '<option value="">尚未設定模型</option>');
    if (models.some(m => m.id === selected)) $(id).value = selected;
  }
}
function testResultRow(provider, model, status, detail = "", result = {}) {
  const kind = status === "成功" ? "" : status === "失敗" ? "error" : status === "測試中" ? "warning" : "neutral";
  const elapsed = result.elapsed_ms == null ? "—" : `${(result.elapsed_ms / 1000).toFixed(2)} 秒`;
  return `<div class="test-result"><div><strong>${provider === "claude" ? "Claude" : "Codex"}</strong><code>${esc(model || "未設定模型")}</code><p>${esc(detail)}</p></div><div class="test-result-meta">${badge(status, kind)}<strong>${elapsed}</strong><small>${result.http_status ? `HTTP ${result.http_status}` : "未取得 HTTP 回應"}</small></div></div>`;
}
$("connection-test-form").addEventListener("submit", async e => {
  e.preventDefault();
  if (testingConnection || !state) return;
  let key = $("test-api-key").value.trim();
  if (!key) return toast("請先輸入 API 金鑰。");
  const endpoint = state.endpoint;
  const models = Object.fromEntries(["claude", "codex"].map(p => [p, $(`test-model-${p}`).value]));
  const rows = {};
  testingConnection = true;
  $("test-api-key").value = "";
  for (const el of $("connection-test-form").elements) el.disabled = true;
  $("test-connection").textContent = "測試中…";
  $("test-run-note").textContent = `測試入口：${endpoint}`;
  const draw = () => $("connection-test-results").innerHTML = ["claude", "codex"].map(p => rows[p]).join("");
  for (const provider of ["claude", "codex"]) rows[provider] = testResultRow(provider, models[provider], "等待測試");
  draw();
  try {
    for (const provider of ["claude", "codex"]) {
      if (!models[provider]) { rows[provider] = testResultRow(provider, "", "略過", "請先到模型管理登錄此來源的模型。"); draw(); continue; }
      rows[provider] = testResultRow(provider, models[provider], "測試中", "正在等待模型回應…"); draw();
      try {
        const result = await api("/manage/test-connection", {key, provider, model:models[provider], endpoint}, false, 75000);
        rows[provider] = testResultRow(provider, result.model, result.success ? "成功" : "失敗", result.message, result);
      } catch (error) {
        rows[provider] = testResultRow(provider, models[provider], "失敗", error.name === "TimeoutError" ? "管理台等待逾時；測試可能仍在執行，請先查看請求紀錄。" : "測試未完成，請確認管理台連線與目前設定後重試。");
      }
      draw();
    }
  } finally {
    key = ""; testingConnection = false;
    for (const el of $("connection-test-form").elements) el.disabled = false;
    $("test-connection").textContent = "測試 Claude 與 Codex";
    $("test-run-note").textContent = `測試完成 ${new Date().toLocaleTimeString("zh-TW", {hour12:false})} · ${endpoint}`;
    renderTestModels();
  }
});
window.addEventListener("pagehide", () => { $("test-api-key").value = ""; });
$("connect-guide").addEventListener("click", guide);
$("recent-logs").addEventListener("click", e => { if (e.target.closest("#empty-connect")) guide(); });
$("copy-endpoint").addEventListener("click", () => copy($("endpoint").value));
$("pause").addEventListener("click", e => run(e.currentTarget, async () => { if (!state) return; await api("/manage/accepting", {accepting:!state.accepting}); await refresh(); }));
$("refresh-auth").addEventListener("click", e => run(e.currentTarget, async () => { await api("/manage/auth", {}); await refresh(); }));
for (const id of ["log-status","log-provider"]) $(id).addEventListener("change", () => refreshLogs().catch(e => toast(e.message)));
$("export").addEventListener("click", e => run(e.currentTarget, async () => { if (await window.BridgePlatform.exportLogs(logQuery(), () => api(`/manage/export?${logQuery()}`, undefined, true))) toast("已匯出目前篩選的中繼資料"); }));
$("clear-logs").addEventListener("click", () => confirmation("清除已結束紀錄", "將清除所有已結束的請求紀錄（包含目前篩選以外的紀錄）。排隊與執行中的工作會保留，此操作無法復原。", "確認清除", async () => { await api("/manage/logs/clear", {}); closeModal(); await refresh(); }));
function fillSettings() { const form = $("settings-form"); for (const [k,v] of Object.entries({...state.settings, startup:state.startup})) { const input = form.elements[k]; if (!input) continue; if (input.type === "checkbox") input.checked = v; else input.value = v; } }
function settingsData() { const values = {...state.settings, startup:state.startup}; for (const input of $("settings-form").elements) { if (!input.name) continue; values[input.name] = input.type === "checkbox" ? input.checked : input.type === "number" ? Number(input.value) : input.value.trim(); } return values; }
$("settings-form").addEventListener("submit", e => { e.preventDefault(); run(document.querySelector('[form="settings-form"]'), async () => { if (!state) throw new Error("請等待管理台連線。"); await api("/manage/settings", settingsData()); toast("設定已儲存；連接埠變更會在重啟後生效。"); await refresh(); }); });
function modelRow(model = {id:"",provider:"claude",native:""}) { return `<div class="model-row"><label>呼叫端模型名稱<input data-model="id" value="${esc(model.id)}" placeholder="anthropic/model-name" required></label><label>來源<select data-model="provider"><option value="claude" ${model.provider === "claude" ? "selected" : ""}>Claude</option><option value="codex" ${model.provider === "codex" ? "selected" : ""}>Codex</option></select></label><label>原生模型 ID<input data-model="native" value="${esc(model.native)}" placeholder="CLI model ID" required></label><button class="icon-button remove-model" aria-label="移除此模型">×</button></div>`; }
function renderModels() { $("model-editor").innerHTML = state.settings.models.map(modelRow).join(""); }
$("add-model").addEventListener("click", () => { $("model-editor").insertAdjacentHTML("beforeend", modelRow()); $("model-editor").lastElementChild.querySelector("input").focus(); });
$("model-editor").addEventListener("click", e => { const button = e.target.closest(".remove-model"); if (button) button.closest(".model-row").remove(); });
$("save-models").addEventListener("click", e => run(e.currentTarget, async () => { if (!state) throw new Error("請等待管理台連線。"); const models = [...document.querySelectorAll(".model-row")].map(row => Object.fromEntries([...row.querySelectorAll("[data-model]")].map(input => [input.dataset.model, input.value.trim()]))); if (!models.length || models.some(m => !m.id || !m.native)) throw new Error("請至少登錄一個模型，並填妥模型名稱與原生 ID。"); await api("/manage/settings", {...state.settings, startup:state.startup, models}); toast("模型對應已儲存"); await refresh(); }));
$("pair-relay").addEventListener("click", () => { modal("裝置配對", '<form id="pair-form" class="modal-form"><p>輸入雲端 Worker 的 DEVICE_KEY。配對 key 會以 Windows DPAPI 或 macOS Keychain 保存。</p><label>裝置配對 key<input name="key" type="password" autocomplete="off" required></label><p id="modal-error" class="inline-error" role="alert"></p><button type="submit" class="primary">儲存配對 key</button></form>'); $("pair-form").addEventListener("submit", e => { e.preventDefault(); modalRun(e.target.querySelector("button"), async () => { await api("/manage/pair", {key:e.target.elements.key.value}); closeModal(); toast("配對 key 已保存，請啟用轉接並儲存設定。"); }); }); });
for (const action of ["start","stop"]) $(`${action}-tunnel`).addEventListener("click", e => run(e.currentTarget, async () => { await api(`/manage/tunnel/${action}`, {}); await refresh(); }));
function shutdown() { confirmation("結束 Bridge", "本機服務將停止，執行中的工作會取消，外部服務也將無法呼叫。若只想關閉管理台，直接關閉視窗或瀏覽器分頁即可。", "結束 Bridge", async () => { await api("/manage/shutdown", {}); stopped = true; closeModal(); $("connection-error").hidden = false; $("connection-error").textContent = "Bridge 正在結束。可關閉此頁；下次請從 Bridge 捷徑啟動。"; $("service-badge").className = "badge neutral"; $("service-badge").textContent = "服務正在停止"; }); }
$("shutdown").addEventListener("click", shutdown);
$("page-settings").insertAdjacentHTML("beforeend", '<button class="secondary danger mobile-shutdown" id="mobile-shutdown">結束 Bridge</button>');
$("mobile-shutdown").addEventListener("click", shutdown);
for (const id of ["recent-logs","keys-list","all-logs"]) $(id).innerHTML = '<div class="loading">正在載入本機資料…</div>';
navigate(location.hash.slice(1)); refresh(); setInterval(refresh, 2500);
