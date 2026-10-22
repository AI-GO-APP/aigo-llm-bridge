// Windows adapter only. No native bridge is used by the browser/Mac frontend.
window.addEventListener('pywebviewready', () => {
  const native = window.pywebview?.api;
  if (!native?.copy_text || !native?.export_logs) return;
  window.BridgePlatform = {
    name: 'windows-webview2', native: true,
    async copyText(text) { if (!(await native.copy_text(text)).ok) throw new Error('Copy failed'); },
    async exportLogs(query) { return (await native.export_logs(String(query))).saved; }
  };
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'secondary compact';
  button.id = 'windows-open-browser'; button.textContent = '用預設瀏覽器開啟';
  button.addEventListener('click', () => native.open_browser());
  document.querySelector('.topbar-right').prepend(button);
});
