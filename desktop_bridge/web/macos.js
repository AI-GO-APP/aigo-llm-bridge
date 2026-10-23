// Mac adapter: native actions are limited to this local management session.
function installMacAdapter() {
  const native = window.pywebview?.api;
  if (!native?.copy_text || !native?.export_logs) return;
  window.BridgePlatform = {
    name: 'macos-wkwebview', native: true,
    async copyText(text) { if (!(await native.copy_text(text)).ok) throw new Error('Copy failed'); },
    async exportLogs(query) { return (await native.export_logs(String(query))).saved; }
  };
}
window.addEventListener('pywebviewready', installMacAdapter);
installMacAdapter();
{
  const section = document.createElement('article');
  section.className = 'card settings-card macos-update-card';
  section.innerHTML = '<div class="section-description"><h2>Mac 安裝與更新</h2><p>裝置設定、來源版本與安全更新。</p></div><div class="settings-fields"><p id="macos-release-status">正在取得版本…</p><div class="row-actions"><button type="button" class="secondary compact" id="macos-browser">用預設瀏覽器開啟</button><button type="button" class="secondary compact" id="macos-update">排空並從本機來源更新</button></div><p>更新採用已記錄的本機原始碼，保留網址、KEY、模型及紀錄，失敗嘗試回復原版。Mac source ZIP 由 GitHub Release 提供；下載新版後，依 Mac 指南選擇新來源更新。目前不提供自動下載更新。</p><p id="macos-update-state" role="status"></p></div>';
  document.querySelector('#settings-form').append(section);
  section.querySelector('#macos-browser').addEventListener('click', event => run(event.currentTarget, () => api('/manage/macos-console/browser', {})));
  section.querySelector('#macos-update').addEventListener('click', event => run(event.currentTarget, async () => {
    if (!window.confirm('更新這台 Mac 的 Bridge？會先排空工作，安裝已記錄的本機來源並重新啟動。')) return;
    await api('/manage/macos-update/apply', {});
    section.querySelector('#macos-update-state').textContent = '正在排空及更新；完成後請從 Bridge 捷徑重新開啟。';
  }));
  setInterval(() => {
    if (!state?.macos_release) return;
    const release = state.macos_release;
    section.querySelector('#macos-release-status').textContent = `Mac ${release.version}／${release.source_commit?.slice(0, 12) || '本機來源'}${state.macos_onboarding?.required ? '／安裝精靈尚未完成（既有 API 繼續供應）' : ''}`;
    section.querySelector('#macos-update').disabled = !release.source_checkout;
    const update = state.macos_update;
    if (update) section.querySelector('#macos-update-state').textContent = update.status === 'completed' ? `已完成來源更新：${update.version}` : update.status === 'failed' ? (update.recovered ? '更新失敗，已啟動原版。' : '更新失敗，請依 Mac 指南檢查原設定檔及服務。') : '來源更新處理中。';
  }, 1000);
}
