// Included only in the Windows Velopack bundle; no changes to the shared/Mac UI.
{
  const target = document.querySelector('#settings-form');
  if (target) {
    const section = document.createElement('article');
    section.className = 'card settings-card windows-update-card';
    section.innerHTML = '<div class="section-description"><h2>Windows 安裝與更新</h2><p>此裝置的安裝版本與專屬更新渠道。</p></div><div class="settings-fields"><p id="windows-release-status">正在讀取版本…</p><div class="row-actions"><button type="button" class="secondary compact" id="windows-setup">開啟 CLI 設定引導</button><button type="button" class="secondary compact" id="windows-check">檢查更新</button><button type="button" class="primary compact" id="windows-apply">排空工作並更新</button></div><p>安裝包未具公發簽章。更新會保留此裝置的網址、KEY 與資料，不會部署 Worker 或變更訂閱登入。</p></div>';
    target.append(section);
    const notice = document.createElement('div');
    notice.className = 'preview-notice';
    notice.hidden = true;
    notice.setAttribute('role', 'status');
    document.querySelector('#main').prepend(notice);
    for (const [id, action] of [['windows-setup','setup'],['windows-check','check'],['windows-apply','apply']]) {
      section.querySelector('#' + id).addEventListener('click', async event => {
        const button = event.currentTarget;
        button.disabled = true;
        try { await api('/manage/windows-update/' + action, {}); await refresh(); }
        catch (_) { section.querySelector('#windows-release-status').textContent = '管理連線已重啟或操作未完成，請從捷徑重新開啟。'; }
        finally { button.disabled = false; }
      });
    }
    setInterval(() => {
      if (!state || !state.windows_release) return;
      const update = state.windows_update || {};
      notice.hidden = !(update.available || update.required);
      notice.textContent = update.required ? '此 Windows 版本需要更新，已暫停新 LLM 工作。請到「連線與設定」檢查並更新；網址、KEY 與紀錄會保留。' : `Windows ${update.latest} 可更新。請到「連線與設定」查看。`;
      document.querySelector('#pause').disabled = !!update.required;
      section.querySelector('#windows-release-status').textContent = `已安裝 ${state.windows_release.version}（核心 ${state.windows_release.core_version}）／${update.status || 'not_checked'}${update.latest ? '／渠道版本 ' + update.latest : ''}${state.windows_onboarding?.required ? '／首次安裝設定尚未完成' : ''}`;
    }, 1000);
  }
}
