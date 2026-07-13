/**
 * content.js
 * ==========
 * Injected into LeetCode problem pages. Responsible for extracting:
 *   - Problem title
 *   - Problem description
 *   - Examples
 *   - Constraints
 *
 * LeetCode's DOM structure changes fairly often, so extraction uses a
 * layered strategy: try modern selectors first, then fall back to more
 * generic heuristics so the extension degrades gracefully instead of
 * breaking outright.
 *
 * Communicates with popup.js via chrome.runtime messaging.
 */

(function () {
  "use strict";

  /**
   * Attempts to locate the problem title using a series of selector
   * fallbacks, since LeetCode frequently changes class names.
   */
  function extractTitle() {
    const selectors = [
      'div[data-cy="question-title"]',
      "a.text-title-large",
      "div.text-title-large",
      "div.css-v3d350",
      "h1",
    ];

    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.trim()) {
        return el.textContent.trim();
      }
    }

    // Fallback: derive title from the URL slug, e.g. /problems/two-sum/
    const match = window.location.pathname.match(/\/problems\/([^/]+)\//);
    if (match && match[1]) {
      return match[1]
        .split("-")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
    }

    return "";
  }

  /**
   * Attempts to locate the main problem description container.
   * Returns cleaned plain text (description + examples + constraints
   * combined, since LeetCode renders them all inside the same panel).
   */
  function extractDescription() {
    const selectors = [
      'div[data-track-load="description_content"]',
      "div.elfjS",
      "div.content__u3I1.question-content__JfgR",
      'div[class*="question-content"]',
    ];

    for (const selector of selectors) {
      const el = document.querySelector(selector);
      if (el && el.textContent.trim().length > 20) {
        return el.innerText.trim();
      }
    }

    return "";
  }

  /**
   * Extracts "Example" blocks from the description text using simple
   * text-based heuristics (since layout classes are unreliable).
   */
  function extractExamples(fullText) {
    if (!fullText) return "";
    const exampleMatches = fullText.match(/Example\s*\d*[\s\S]*?(?=(Example\s*\d*|Constraints|$))/gi);
    return exampleMatches ? exampleMatches.join("\n\n").trim() : "";
  }

  /**
   * Extracts the "Constraints" section from the description text.
   */
  function extractConstraints(fullText) {
    if (!fullText) return "";
    const constraintsMatch = fullText.match(/Constraints:[\s\S]*/i);
    return constraintsMatch ? constraintsMatch[0].trim() : "";
  }

  /**
   * Determines whether the current page looks like a valid LeetCode
   * problem page (as opposed to the problem list, home page, etc.)
   */
  function isValidProblemPage() {
    return /\/problems\/[^/]+\/?/.test(window.location.pathname);
  }

  /**
   * Gathers all extracted problem data into a single object.
   */
  function extractProblemData() {
    if (!isValidProblemPage()) {
      return { valid: false, error: "Not a LeetCode problem page." };
    }

    const title = extractTitle();
    const description = extractDescription();

    if (!description) {
      return {
        valid: false,
        error: "Could not find problem description on this page.",
      };
    }

    const examples = extractExamples(description);
    const constraints = extractConstraints(description);

    return {
      valid: true,
      title,
      description,
      examples,
      constraints,
      url: window.location.href,
    };
  }

  // Listen for extraction requests coming from the popup.
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message && message.type === "EXTRACT_PROBLEM") {
      try {
        const data = extractProblemData();
        sendResponse(data);
      } catch (err) {
        sendResponse({
          valid: false,
          error: `Extraction failed: ${err.message}`,
        });
      }
    }
    // Return true to indicate we may respond asynchronously.
    return true;
  });
})();
