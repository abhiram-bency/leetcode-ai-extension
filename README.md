# LeetCode AI Assistant

A Chrome Extension + FastAPI backend that extracts LeetCode problems straight
from the page you're viewing and generates a solution, complete with time and
space complexity estimates — all without requiring a single API key out of
the box.

---

## 1. Project Overview

LeetCode AI Assistant is built around a **provider-agnostic solver
architecture**. The extension scrapes the problem you're looking at, sends
it to a local FastAPI backend, and the backend hands it off to a `BaseSolver`
implementation. Today that implementation is `MockSolver` — a fully offline,
deterministic solver that requires zero configuration. Tomorrow it could be
Gemini, OpenAI, Claude, Ollama, or any REST-based LLM, and **not a single
line outside of `solver.py` needs to change**.

Core features:

- 🔍 Detects LeetCode problem pages and extracts title, description,
  examples, and constraints via DOM parsing.
- 🧠 Sends extracted data to a local FastAPI backend for solving.
- 🧩 Provider-agnostic solver interface (`BaseSolver` / `MockSolver`).
- 💻 Polished dark-themed popup UI with live backend status.
- 📋 One-click code copy, language selector, and complexity display.
- 🛡️ Friendly error handling for offline backend, invalid pages, and
  network failures.

---

## 2. Architecture Diagram (ASCII)

```
┌─────────────────────────────┐         ┌────────────────────────────────┐
│         Chrome Tab          │         │        Chrome Extension         │
│  (leetcode.com/problems/*)  │         │                                  │
│                              │  DOM    │  content.js                     │
│   Problem Title              │◄───────┤   - extracts title/desc/         │
│   Description / Examples /   │  scrape │     examples/constraints        │
│   Constraints                │         │                                  │
└─────────────────────────────┘         │  popup.js                        │
                                          │   - orchestrates flow            │
                                          │   - calls backend /solve         │
                                          │  popup.html / popup.css          │
                                          │   - renders results              │
                                          └───────────────┬──────────────────┘
                                                           │ HTTP (fetch)
                                                           ▼
                                          ┌────────────────────────────────┐
                                          │        FastAPI Backend          │
                                          │                                  │
                                          │  app.py                          │
                                          │   - POST /solve                  │
                                          │   - GET  /health                 │
                                          │                                  │
                                          │  solver.py                       │
                                          │   - BaseSolver (interface)        │
                                          │   - MockSolver (default, offline) │
                                          │   - [future] Gemini/OpenAI/       │
                                          │     Claude/Ollama/REST solvers    │
                                          │                                  │
                                          │  prompt.py                        │
                                          │   - shared prompt construction    │
                                          └────────────────────────────────┘
```

---

## 3. Folder Structure

```
leetcode-ai-extension/
│
├── backend/
│   ├── app.py              # FastAPI app: /solve, /health routes
│   ├── solver.py           # BaseSolver + MockSolver + provider TODOs
│   ├── prompt.py           # Shared prompt-building utility
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Placeholder env vars for future providers
│
├── chrome-extension/
│   ├── manifest.json       # Manifest V3 config
│   ├── popup.html          # Popup UI markup
│   ├── popup.css           # Dark "compiler console" theme
│   ├── popup.js            # Popup logic: extraction, API calls, rendering
│   ├── content.js          # Injected script: DOM extraction from LeetCode
│   ├── background.js       # Service worker
│   └── icons/              # Extension icons (16/48/128 px)
│
└── README.md
```

---

## 4. Installation

### Prerequisites
- Python 3.9+
- Google Chrome (or any Chromium-based browser supporting Manifest V3)

### Clone / copy the project
Place the `leetcode-ai-extension/` folder anywhere on your machine.

---

## 5. Running the Backend

```bash
cd leetcode-ai-extension/backend

# (Recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app:app --reload --port 8000
```

Once running, verify it's alive:

```bash
curl http://localhost:8000/health
# {"status":"ok","solver":"MockSolver"}
```

Interactive API docs are available at `http://localhost:8000/docs`.

> No `.env` file or API key is required to run the backend — `MockSolver` is
> fully self-contained. `.env.example` is provided only for when you wire up
> a real provider later.

---

## 6. Loading the Chrome Extension

1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode** (top-right toggle).
3. Click **Load unpacked**.
4. Select the `leetcode-ai-extension/chrome-extension` folder.
5. Pin the extension for easy access (puzzle-piece icon → pin).
6. Navigate to any LeetCode problem, e.g.
   `https://leetcode.com/problems/two-sum/`.
7. Click the extension icon. You should see the problem title populate and
   the backend status indicator turn green (make sure the backend from
   step 5 is running).
8. Click **Generate Solution** to fetch a mock solution, then use
   **Copy Code** to copy it to your clipboard.

---

## 7. Future Work

The entire point of the `BaseSolver` abstraction is that adding a real
provider only touches `solver.py` (and optionally `.env`). Below are the
exact integration points already stubbed with TODO comments in
`backend/solver.py`.

### Adding Gemini
1. `pip install google-generativeai`
2. Implement `GeminiSolver(BaseSolver)` using `google.generativeai`.
3. Set `GEMINI_API_KEY` in `.env`.
4. Update `get_solver()` to `return GeminiSolver(api_key=os.getenv("GEMINI_API_KEY"))`.

### Adding OpenAI
1. `pip install openai`
2. Implement `OpenAISolver(BaseSolver)` using the `openai` SDK's chat
   completions endpoint.
3. Set `OPENAI_API_KEY` in `.env`.
4. Update `get_solver()` to return an `OpenAISolver` instance.

### Adding Claude (Anthropic)
1. `pip install anthropic`
2. Implement `ClaudeSolver(BaseSolver)` using `anthropic.Anthropic().messages.create(...)`.
3. Set `ANTHROPIC_API_KEY` in `.env`.
4. Update `get_solver()` to return a `ClaudeSolver` instance.

### Adding Ollama (local LLM, no API key needed)
1. Install and run [Ollama](https://ollama.com) locally.
2. Implement `OllamaSolver(BaseSolver)` calling `POST /api/generate` on
   `http://localhost:11434`.
3. Update `get_solver()` to return an `OllamaSolver` instance.

### Adding any generic REST API
1. Implement `RestApiSolver(BaseSolver)` that POSTs the prompt (built via
   `prompt.build_solver_prompt`) to your endpoint and parses the response.
2. Set `SOLVER_API_URL` / `SOLVER_API_KEY` in `.env`.
3. Update `get_solver()` to return a `RestApiSolver` instance.

In every case above, **no changes are required** to `app.py`, `prompt.py`,
or any Chrome extension file — the contract defined by `BaseSolver` is all
the rest of the system depends on.

---

## 8. Screenshots

> Placeholders — replace with actual screenshots once you've loaded the
> extension.

- `docs/screenshot-popup-idle.png` — Popup before generating a solution
- `docs/screenshot-popup-result.png` — Popup showing a generated solution
- `docs/screenshot-backend-docs.png` — FastAPI `/docs` Swagger UI

---

## 9. Error Handling Summary

| Scenario                          | Behavior                                                        |
|-----------------------------------|-------------------------------------------------------------------|
| Backend offline                   | Status dot turns red; "Generate" shows a clear offline error     |
| Not on a LeetCode problem page    | Popup shows "No problem detected" / extraction error message     |
| Missing problem description       | Backend returns HTTP 400 with a descriptive error message         |
| Empty solver response              | Backend returns HTTP 502; popup surfaces a friendly error         |
| Network failure during fetch      | popup.js catches the exception and displays it in the error banner |

---

## License

This project is provided as-is for educational and personal productivity
use. Respect LeetCode's terms of service when using automated tooling on
their platform.
