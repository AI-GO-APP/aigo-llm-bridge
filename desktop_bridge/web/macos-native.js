// Fixed native surface for Cocoa. Closures preserve script-src 'self' without eval/new Function.
window.pywebview._createApi = function (functions) {
  const allowed = new Set(['copy_text', 'export_logs', 'open_browser']);
  for (const item of functions) {
    const name = item.func;
    if (!allowed.has(name)) continue;
    window.pywebview._returnValuesCallbacks[name] = {};
    window.pywebview.api[name] = function (...args) {
      const id = String(Math.random()).slice(2);
      const promise = new Promise((resolve, reject) => window.pywebview._checkValue(name, resolve, reject, id));
      window.pywebview._jsApiCallback(name, args, id);
      return promise;
    };
  }
};
