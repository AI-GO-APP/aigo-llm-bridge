// Shared frontend contract. Native shells install an adapter; browser stays usable.
"use strict";
window.BridgePlatform = {
  name: "browser",
  native: false,
  copyText: text => navigator.clipboard.writeText(text),
  async exportLogs(query, load) {
    const blob = await load();
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = "bridge-request-metadata.csv"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    return true;
  }
};
