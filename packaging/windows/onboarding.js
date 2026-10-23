// Windows-only installer workflow. No credentials or raw model output in storage.
{
  const wizard = document.createElement('dialog');
  wizard.id = 'windows-onboarding';
  wizard.setAttribute('aria-labelledby', 'onboarding-title');
  wizard.innerHTML = `<div class="modal-header"><div><div class="eyebrow">DEVICE SETUP</div><h2 id="onboarding-title">完成這台電腦的安裝設定</h2></div><button type="button" class="icon-button" id="ob-close" aria-label="關閉安裝設定">×</button></div>
    <div class="onboarding-body"><p>每台電腦首次安裝需完成一次；完成後日常啟動直接進主畫面。中途關窗可稍後續接，網址與 KEY 不會因此改變。</p>
    <nav id="ob-steps" class="row-actions" aria-label="安裝步驟">${['插電與休眠','訂閱授權','Cloudflare','Worker 入口','KEY 與交付'].map((text,i)=>`<button type="button" class="secondary compact" data-ob-step="${i}">${i+1}. ${text}</button>`).join('')}</nav>
    <p id="ob-job" role="status" aria-live="polite">正在取得安裝狀態…</p>
    <section data-ob-panel="0"><h3>1. 同意插電不自動休眠</h3><p>建立專用電源計畫，只把支援的插電自動睡眠、休眠與無人值守睡眠設為永不。保留原計畫及電池設定；螢幕關閉、Win+L、自動鎖定、螢幕保護、動態鎖定與組織安全政策維持原狀。</p>
      <p>鎖定不等於休眠。服務在電腦持續運作且目前使用者未登出的情況下可在背景接單。手動睡眠、闔蓋、實體按鍵、關機及斷電仍依 Windows 原設定處理，可能中斷 API。</p>
      <label class="check-label"><input id="ob-power-consent" type="checkbox">我同意只調整上述插電自動休眠設定，保留電池與鎖定設定。</label>
      <p id="ob-power-state" role="status"></p><div class="row-actions"><button type="button" id="ob-power" class="primary">同意並套用、讀回驗證</button><button type="button" id="ob-power-admin" class="secondary">電源權限不足時以管理員套用（UAC）</button><button type="button" id="ob-restore" class="secondary">還原原電源計畫</button><button type="button" id="ob-restore-admin" class="secondary">以管理員權限還原電源（UAC）</button></div>
      <p>優先使用一般權限；只有電源計畫權限不足時才由本人選擇 UAC。程式不調整鎖定登錄值，不覆寫組織休眠政策。未支援項目會列出；請依自己的裝置檢查廠商休眠工具。</p></section>
    <section data-ob-panel="1" hidden><h3>2. 本地 LLM 訂閱授權</h3><p>預設使用 Codex 的 ChatGPT 訂閱；至少一個來源可用即可。登入僅在你點選後啟動官方授權，不會登出、切換帳戶或打斷正在使用的 CLI。</p>
      <div class="field-grid"><div><h4>Codex</h4><p id="ob-codex-state">尚未檢查</p><button type="button" id="ob-login-codex" class="secondary">開啟 Codex 訂閱登入</button><p>未安裝時在自己的 PowerShell 執行：</p><pre class="code-block">npm install -g @openai/codex\ncodex login\ncodex login status</pre><p>選 ChatGPT 登入；不輸入 OpenAI API key。</p></div>
      <div><h4>Claude Code（選用）</h4><p id="ob-claude-state">尚未檢查</p><button type="button" id="ob-login-claude" class="secondary">開啟 Claude 訂閱登入</button><p>先依 code.claude.com/docs/en/setup 安裝，再執行：</p><pre class="code-block">claude auth login\nclaude auth status</pre><p>沿用 Claude.ai 訂閱。已登入者不會再次登入。</p></div></div><p>Node.js 需 22 以上。授權或換訂閱不改變此裝置的 URL 和 KEY。</p><details><summary>進階：指定已安裝的原生 CLI 路徑</summary><label>Codex<input id="ob-codex-path" placeholder="自動偵測"></label><label>Claude<input id="ob-claude-path" placeholder="自動偵測"></label><button type="button" id="ob-cli-paths" class="secondary">保存 CLI 路徑</button></details></section>
    <section data-ob-panel="2" hidden><h3>3. 登入自己的 Cloudflare</h3><p>安裝者自己管理、付費及更新 Worker；發布方不代管。先安裝 Node.js 24.22.1 以上（或 22.23.4 以上）與固定版本 Wrangler：</p><pre class="code-block">npm install -g wrangler@4.152.0\nwrangler login\nwrangler whoami --json</pre><p>瀏覽器會開啟 Cloudflare OAuth。不要把 OAuth token、Global API key 或帳號密碼貼到 Bridge。已授權時沿用，絕不自動登出。</p><button type="button" id="ob-login-cloudflare" class="primary">開啟 Cloudflare 官方登入</button><p id="ob-cf-state" role="status">尚未檢查</p></section>
    <section data-ob-panel="3" hidden><h3>4. 部署裝置專屬 Worker</h3><p>登入後明確選擇你自己的帳戶。一鍵部署會建立固定 Worker、以加密裝置憑證配對並驗證 HTTPS；同設定檔重試仍保留原 URL 和 KEY。</p>
      <label>Cloudflare 帳戶<select id="ob-account"><option value="">請先重新檢查登入</option></select></label>
      <label class="check-label"><input id="ob-deploy-consent" type="checkbox">我確認選定的是自有帳戶，授權在此帳戶建立／更新這台電腦的 Worker。</label>
      <div class="row-actions"><button type="button" id="ob-deploy" class="primary">一鍵部署並綁定</button><button type="button" id="ob-prompt" class="secondary">複製 AI IDE 協作 prompt</button></div><p>協作 prompt 交給你的 AI IDE；不呼叫本地 LLM CLI 來替你執行部署。它不含憑證或 client KEY。</p>
      <p id="ob-deployment" role="status"></p></section>
    <section data-ob-panel="4" hidden><h3>5. 取得長效 KEY、實測與交付</h3><p>新 KEY 預設模型全開。完整 KEY 只在這次畫面及剪貼簿出現，程式只存 hash；請存到呼叫服務的 secret 管理。關窗後無法找回原文，可貼回已保存的 KEY。</p>
      <div class="row-actions"><button type="button" id="ob-create-key" class="secondary">建立一把長效 KEY</button><button type="button" id="ob-copy-key" class="secondary">複製 KEY</button><button type="button" id="ob-copy-handoff" class="primary">複製給第三方 AI IDE 的完整串接訊息</button></div>
      <label>固定 endpoint<input id="ob-endpoint" readonly spellcheck="false"></label><label>本次 KEY<input id="ob-key" type="password" autocomplete="off" spellcheck="false" maxlength="256"></label>
      <label>實測模型<select id="ob-model"></select></label><button type="button" id="ob-verify" class="primary">發送一筆真 HTTPS 測試（會用少量訂閱額度）</button><p id="ob-verification" role="status">需取得 PONG 與數值型 usage.cost 才算通過；不自動重試。</p>
      <label class="check-label"><input id="ob-key-saved" type="checkbox">我已將 KEY 保存到自己的安全位置。</label><label class="check-label"><input id="ob-handoff-saved" type="checkbox">我已複製完整 endpoint／KEY／模型串接訊息。</label><button type="button" id="ob-finish" class="primary">完成安裝，進入主畫面</button></section>
    <div class="onboarding-footer row-actions"><button type="button" id="ob-refresh" class="secondary">重新檢查登入及設定</button><button type="button" id="ob-back" class="secondary">上一步</button><button type="button" id="ob-next" class="primary">下一步</button><button type="button" id="ob-defer" class="secondary">暫存進度，前往進階設定</button></div></div>`;
  document.body.append(wizard);
  const setup = document.createElement('button');
  setup.type = 'button'; setup.className = 'secondary compact'; setup.id = 'windows-open-onboarding'; setup.textContent = '安裝設定精靈';
  document.querySelector('.windows-update-card .row-actions').prepend(setup);
  let step = 0, prompted = false, closeAfterComplete = false, copiedHandoff = false, lastAccounts = '', lastModels = '', handoff = '', pathsFilled = false, opening = false;
  const el = id => wizard.querySelector('#' + id);
  function showStep(next) {
    step = Math.max(0, Math.min(4, next));
    wizard.querySelectorAll('[data-ob-panel]').forEach(panel => panel.hidden = Number(panel.dataset.obPanel) !== step);
    wizard.querySelectorAll('[data-ob-step]').forEach(button => button.setAttribute('aria-current', Number(button.dataset.obStep) === step ? 'step' : 'false'));
    el('ob-back').disabled = step === 0; el('ob-next').hidden = step === 4;
  }
  async function action(name, data = {}) {
    const result = await api('/manage/windows-onboarding/' + name, data);
    if (result.code === 'busy') throw new Error('另一個安裝步驟仍在執行，請稍候。');
    await refresh(); return result;
  }
  function bind(id, callback) { el(id).addEventListener('click', event => run(event.currentTarget, callback)); }
  setup.addEventListener('click', () => { closeAfterComplete = false; wizard.showModal(); action('refresh').catch(error => toast(error.message)); });
  el('ob-close').addEventListener('click', () => { wizard.close(); el('ob-key').value = ''; handoff = ''; });
  wizard.addEventListener('close', () => { el('ob-key').value = ''; handoff = ''; });
  wizard.querySelectorAll('[data-ob-step]').forEach(button => button.addEventListener('click', () => showStep(Number(button.dataset.obStep))));
  bind('ob-next', () => showStep(step + 1)); bind('ob-back', () => showStep(step - 1));
  bind('ob-defer', () => { fillSettings(); renderModels(); wizard.close(); navigate('settings'); toast('安裝尚未完成，下次啟動會繼續。可先調整模型／CLI，或結束 Bridge 讓新安裝工具的 PATH 生效；請保存 KEY。'); });
  bind('ob-refresh', () => action('refresh'));
  bind('ob-cli-paths', () => action('cli-paths', {codex_path:el('ob-codex-path').value, claude_path:el('ob-claude-path').value}));
  for (const provider of ['codex','claude','cloudflare']) bind('ob-login-' + provider, () => action('login', {provider}));
  bind('ob-power', () => action('power', {consent:el('ob-power-consent').checked}));
  bind('ob-power-admin', () => action('power-admin', {consent:el('ob-power-consent').checked}));
  bind('ob-restore', () => action('restore-power'));
  bind('ob-restore-admin', () => action('restore-power-admin', {consent:el('ob-power-consent').checked}));
  bind('ob-deploy', () => action('deploy', {account_id:el('ob-account').value, consent:el('ob-deploy-consent').checked}));
  bind('ob-prompt', async () => { const result = await action('prompt'); await copy(result.prompt); });
  bind('ob-create-key', async () => {
    if (el('ob-key').value) throw new Error('請先保存目前 KEY；建立新 KEY 不會自動撤銷前一把。');
    const result = await action('create-key'); el('ob-key').value = result.token; handoff = result.integration.prompt;
    copiedHandoff = false; el('ob-key-saved').checked = false; el('ob-handoff-saved').checked = false;
  });
  bind('ob-copy-key', async () => { if (!el('ob-key').value) throw new Error('請先建立或貼入已保存的 KEY。'); await copy(el('ob-key').value); });
  bind('ob-copy-handoff', async () => {
    if (!el('ob-key').value) throw new Error('請先建立或貼入已保存的 KEY。');
    const message = (await api('/manage/handoff?model=' + encodeURIComponent(el('ob-model').value))).prompt + '\nLLM_BRIDGE_KEY=' + el('ob-key').value;
    // Do not mark copied when the platform clipboard operation fails.
    await window.BridgePlatform.copyText(message); copiedHandoff = true; toast('已複製完整串接訊息，請存入第三方服務的 secret。');
  });
  bind('ob-verify', () => action('verify', {key:el('ob-key').value, model:el('ob-model').value}));
  bind('ob-finish', async () => {
    if (!copiedHandoff) throw new Error('請先複製完整串接訊息。');
    await action('finish', {key_saved:el('ob-key-saved').checked, handoff_copied:el('ob-handoff-saved').checked, model:el('ob-model').value});
    fillSettings(); renderModels(); closeAfterComplete = true; wizard.close(); toast('安裝設定完成；下次啟動直接進主畫面。');
  });
  el('ob-key').addEventListener('input', () => { handoff = ''; copiedHandoff = false; });
  el('ob-model').addEventListener('change', () => { copiedHandoff = false; el('ob-handoff-saved').checked = false; });
  function paint() {
    const ob = state?.windows_onboarding;
    if (!ob) return;
    if (!prompted) {
      prompted = true;
      if (ob.required) { wizard.showModal(); action('refresh').catch(error => toast(error.message)); }
    }
    if (ob.open_requested && !opening) {
      opening = true; closeAfterComplete = false;
      if (!wizard.open) wizard.showModal();
      api('/manage/windows-onboarding/opened', {}).catch(() => { opening = false; });
    } else if (!ob.open_requested) opening = false;
    if (closeAfterComplete) return;
    el('ob-close').hidden = ob.required;
    wizard.oncancel = event => { if (state?.windows_onboarding?.required) event.preventDefault(); };
    const job = ob.job || {}, busy = job.status === 'running';
    const errors = {permission_required:'權限不足或 UAC 未允許；可明確點選管理員權限按鈕，或請裝置管理員處理。',operation_failed:'步驟尚未完成。請檢查 CLI 安裝／登入、原帳戶權限、網路或管理政策後重新檢查；不要刪除設定檔重來。'};
    el('ob-job').textContent = busy ? `正在執行 ${job.action}，可以等待或關閉視窗稍後續接…` : job.status === 'failed' ? errors[job.code] || '操作未完成' : job.status === 'completed' ? `${job.action} 已完成，請核對本步驟結果。` : '依序完成五個步驟。';
    for (const id of ['ob-refresh','ob-power','ob-power-admin','ob-restore','ob-restore-admin','ob-deploy','ob-login-codex','ob-login-claude','ob-login-cloudflare','ob-verify','ob-create-key','ob-finish','ob-cli-paths']) el(id).disabled = busy;
    for (const p of ['codex','claude']) el('ob-' + p + '-state').textContent = ob.subscriptions[p] === true ? '訂閱已登入，將沿用現況' : ob.subscriptions[p] === false ? '尚未就緒，請安裝並完成訂閱登入' : '尚未檢查';
    if (!pathsFilled) { pathsFilled = true; for (const p of ['codex','claude']) el('ob-' + p + '-path').value = state.settings[p + '_path'] || ''; }
    el('ob-power-state').textContent = ob.power.verified ? '插電自動休眠設定已套用並讀回；電池、螢幕與鎖定設定保留。' : `尚未通過電源設定${ob.power.blockers?.length ? '；有組織休眠政策：' + ob.power.blockers.join('、') : ''}${ob.power.changed?.length ? '；電源計畫已被更改，請還原後重新套用。' : ''}`;
    if (ob.power.unsupported?.length) el('ob-power-state').textContent += ' 未支援項目：' + ob.power.unsupported.join('、') + '；請依裝置確認休眠行為。';
    el('ob-cf-state').textContent = ob.accounts.length ? `已授權 ${ob.accounts.length} 個帳戶；下一步需明確選定。` : '尚未取得可用 Cloudflare 帳戶，請登入後按重新檢查。';
    const accounts = JSON.stringify([ob.accounts, ob.bound_account]);
    if (accounts !== lastAccounts) {
      lastAccounts = accounts;
      el('ob-account').innerHTML = '<option value="">請明確選擇自有帳戶</option>' + ob.accounts.map(a => `<option value="${esc(a.id)}" ${ob.bound_account && a.id !== ob.bound_account ? 'disabled' : ''}>${esc(a.name)} (${esc(a.id)})</option>`).join('');
      if (ob.bound_account) el('ob-account').value = ob.bound_account;
    }
    el('ob-deployment').textContent = ob.deployment.public_url ? `固定入口：${ob.deployment.public_url}；裝置${ob.deployment.device_paired ? '已配對' : '尚未配對'}；Relay：${state.relay}` : '尚未部署及配對。';
    el('ob-endpoint').value = ob.deployment.public_url ? ob.deployment.public_url + '/api/v1' : '';
    const models = JSON.stringify(state.settings.models);
    if (models !== lastModels) { lastModels = models; el('ob-model').innerHTML = state.settings.models.map(m => `<option value="${esc(m.id)}">${esc(m.id)}</option>`).join(''); el('ob-model').value = state.settings.models.find(m=>m.provider==='codex')?.id || state.settings.models[0]?.id; }
    const verified = ob.verification;
    if (verified) el('ob-verification').textContent = verified.success ? `真 HTTPS 已取得 PONG；usage.cost = ${verified.cost_usd} USD（牌價估值）。` : `真 HTTPS 尚未通過：${verified.code}／HTTP ${verified.http_status ?? '—'}，不會自動重試。`;
    else el('ob-verification').textContent = '需取得 PONG 與數值型 usage.cost 才算通過；不自動重試。';
  }
  showStep(0); setInterval(paint, 300);
}
