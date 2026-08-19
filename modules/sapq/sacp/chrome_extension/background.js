// SA-CP Chrome Extension Background Service Worker (v1.0)
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.runtime.onInstalled.addListener(() => {
  console.log("🚀 SA-CP Sovereign Co-Pilot Extension Installed Successfully!");
});
