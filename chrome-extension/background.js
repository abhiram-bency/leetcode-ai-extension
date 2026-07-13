/**
 * background.js
 * =============
 * Manifest V3 service worker. Currently handles lightweight lifecycle
 * logging and acts as a message relay hub in case future features need
 * a persistent background context (e.g., caching last-solved problems).
 */

chrome.runtime.onInstalled.addListener(() => {
  console.log("[LeetCode AI Assistant] Extension installed.");
});

// Placeholder relay: if popup.js ever needs to talk to content.js
// through the background worker (rather than directly), this listener
// can be extended. Currently popup.js messages content.js directly via
// chrome.tabs.sendMessage, so this is mostly here for extensibility.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.type === "PING") {
    sendResponse({ type: "PONG" });
  }
  return true;
});
