/**
 * popup.js
 * ========
 * Orchestrates the extension popup:
 *   1. Checks backend health (/health) to show online/offline status.
 *   2. Asks content.js to extract problem data from the active tab.
 *   3. Sends extracted data to the backend's /solve endpoint.
 *   4. Renders the generated code + complexity results.
 *   5. Handles all error states with user-friendly messages.
 */

const BACKEND_BASE_URL = "http://localhost:8000";

// -------------------- DOM References --------------------
const statusDot = document.getElementById("status-dot");
const statusLabel = document.getElementById("status-label");
const problemTitleEl = document.getElementById("problem-title");
const languageSelect = document.getElementById("language-select");
const generateBtn = document.getElementById("generate-btn");
const generateBtnText = document.getElementById("generate-btn-text");
const spinner = document.getElementById("spinner");
const errorBanner = document.getElementById("error-banner");
const resultCard = document.getElementById("result-card");
const codeOutput = document.getElementById("code-output");
const timeComplexityEl = document.getElementById("time-complexity");
const spaceComplexityEl = document.getElementById("space-complexity");
const copyBtn = document.getElementById("copy-btn");

// Holds the most recently extracted problem so "Generate" can reuse it.
let currentProblem = null;

/**
 * Utility: show an error message in the banner and hide previous results.
 */
function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove("hidden");
}

function clearError() {
  errorBanner.textContent = "";
  errorBanner.classList.add("hidden");
}

/**
 * Toggle the loading state of the Generate button.
 */
function setLoading(isLoading) {
  generateBtn.disabled = isLoading;
  spinner.classList.toggle("hidden", !isLoading);
  generateBtnText.textContent = isLoading ? "Generating..." : "Generate Solution";
}

/**
 * Checks backend availability via GET /health and updates the status
 * indicator in the header accordingly.
 */
async function checkBackendStatus() {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/health`, { method: "GET" });
    if (!response.ok) throw new Error("Non-200 response");

    statusDot.classList.remove("offline");
    statusDot.classList.add("online");
    statusLabel.textContent = "Backend online";
    return true;
  } catch (err) {
    statusDot.classList.remove("online");
    statusDot.classList.add("offline");
    statusLabel.textContent = "Backend offline";
    return false;
  }
}

/**
 * Sends a message to content.js in the active tab requesting problem
 * extraction. Returns the extraction result or an error object.
 */
function requestProblemExtraction() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];

      if (!activeTab || !activeTab.url || !activeTab.url.includes("leetcode.com/problems/")) {
        resolve({
          valid: false,
          error: "Please open a LeetCode problem page (leetcode.com/problems/...) to use this extension.",
        });
        return;
      }

      chrome.tabs.sendMessage(activeTab.id, { type: "EXTRACT_PROBLEM" }, (response) => {
        if (chrome.runtime.lastError) {
          // Common cause: content script not injected yet (e.g., page not fully loaded).
          resolve({
            valid: false,
            error: "Could not communicate with the LeetCode page. Try refreshing the tab.",
          });
          return;
        }
        resolve(response || { valid: false, error: "No response from page." });
      });
    });
  });
}

/**
 * Loads the current problem's title into the popup UI (called on popup
 * open, before the user clicks "Generate").
 */
async function initializeProblemPreview() {
  const extraction = await requestProblemExtraction();

  if (!extraction.valid) {
    problemTitleEl.textContent = "No problem detected";
    currentProblem = null;
    return;
  }

  currentProblem = extraction;
  problemTitleEl.textContent = extraction.title || "Untitled Problem";
}

/**
 * Calls the backend /solve endpoint with the extracted problem data.
 */
async function callSolveApi(problem, language) {
  const combinedDescription = [
    problem.description,
    problem.examples ? `\n${problem.examples}` : "",
    problem.constraints ? `\n${problem.constraints}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  const response = await fetch(`${BACKEND_BASE_URL}/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: problem.title || "",
      description: combinedDescription,
      language,
    }),
  });

  if (!response.ok) {
    let detail = "The backend returned an error.";
    try {
      const errJson = await response.json();
      detail = errJson.detail || detail;
    } catch (_) {
      /* ignore parse failure, use default message */
    }
    throw new Error(detail);
  }

  return response.json();
}

/**
 * Main "Generate Solution" click handler. Ties together extraction,
 * backend status check, API call, and UI rendering.
 */
async function handleGenerateClick() {
  clearError();
  resultCard.classList.add("hidden");

  const backendOnline = await checkBackendStatus();
  if (!backendOnline) {
    showError(
      "Backend is offline. Start it with: uvicorn app:app --reload (see README) and try again."
    );
    return;
  }

  // Re-extract in case the user navigated/edited since popup opened.
  const extraction = await requestProblemExtraction();
  if (!extraction.valid) {
    showError(extraction.error || "Could not extract problem data from this page.");
    return;
  }
  currentProblem = extraction;
  problemTitleEl.textContent = extraction.title || "Untitled Problem";

  setLoading(true);
  try {
    const language = languageSelect.value;
    const result = await callSolveApi(currentProblem, language);

    codeOutput.textContent = result.code || "// No code returned.";
    timeComplexityEl.textContent = result.time_complexity || "-";
    spaceComplexityEl.textContent = result.space_complexity || "-";
    resultCard.classList.remove("hidden");
  } catch (err) {
    showError(`Failed to generate solution: ${err.message}`);
  } finally {
    setLoading(false);
  }
}

/**
 * Copies the generated code to the clipboard and gives brief visual
 * feedback on the Copy button.
 */
async function handleCopyClick() {
  const code = codeOutput.textContent;
  if (!code) return;

  try {
    await navigator.clipboard.writeText(code);
    copyBtn.textContent = "Copied!";
    copyBtn.classList.add("copied");
    setTimeout(() => {
      copyBtn.textContent = "Copy Code";
      copyBtn.classList.remove("copied");
    }, 1500);
  } catch (err) {
    showError("Could not copy code to clipboard.");
  }
}

// -------------------- Event Wiring --------------------
generateBtn.addEventListener("click", handleGenerateClick);
copyBtn.addEventListener("click", handleCopyClick);

// -------------------- Popup Initialization --------------------
document.addEventListener("DOMContentLoaded", async () => {
  await checkBackendStatus();
  await initializeProblemPreview();
});
