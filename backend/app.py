"""
app.py
======
FastAPI backend for the LeetCode AI Assistant Chrome Extension.

Exposes:
    GET  /health   -> simple health-check used by the extension popup
                       to show an "online/offline" backend status.
    POST /solve    -> accepts problem title/description/language and
                       returns generated code + complexity estimates.

The backend is fully provider-agnostic: it delegates all "solving" logic
to whatever solver `get_solver()` (see solver.py) returns. By default
this is MockSolver, so the entire system runs with zero API keys.
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from solver import get_solver, SolverResult

# ---------------------------------------------------------------------
# Environment & Logging
# ---------------------------------------------------------------------
load_dotenv()  # Loads variables from .env if present (used by future providers)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leetcode-ai-assistant")

# ---------------------------------------------------------------------
# FastAPI App Setup
# ---------------------------------------------------------------------
app = FastAPI(
    title="LeetCode AI Assistant API",
    description="Provider-agnostic backend that generates solutions for LeetCode problems.",
    version="1.0.0",
)

# Allow requests from the Chrome extension (extension origins are
# chrome-extension://<id>). We keep CORS permissive here since this is a
# local developer tool; tighten this for any production deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the solver once at startup. Because BaseSolver defines a
# stable interface, swapping providers never requires touching this file.
solver = get_solver()


# ---------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------
class SolveRequest(BaseModel):
    title: str = Field(default="", description="LeetCode problem title")
    description: str = Field(default="", description="Full problem description")
    language: str = Field(default="python", description="Target programming language")


class SolveResponse(BaseModel):
    code: str
    time_complexity: str
    space_complexity: str


class HealthResponse(BaseModel):
    status: str
    solver: str


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Lightweight health-check endpoint. The Chrome extension polls this
    to display an "online"/"offline" status indicator in the popup.
    """
    return HealthResponse(status="ok", solver=solver.__class__.__name__)


@app.post("/solve", response_model=SolveResponse)
def solve_problem(payload: SolveRequest):
    """
    Accepts a LeetCode problem's title/description/language and returns
    a generated solution with time and space complexity estimates.
    """
    title = (payload.title or "").strip()
    description = (payload.description or "").strip()
    language = (payload.language or "python").strip()

    if not description:
        # Missing problem description -- return a clear, actionable error.
        raise HTTPException(
            status_code=400,
            detail="Problem description is empty. Please open a valid LeetCode "
                   "problem page and try again.",
        )

    try:
        result: SolverResult = solver.solve(
            title=title,
            description=description,
            language=language,
        )
    except Exception as exc:  # noqa: BLE001 - surface a friendly error to the client
        logger.exception("Solver failed to generate a solution")
        raise HTTPException(
            status_code=500,
            detail=f"Solver failed to generate a solution: {exc}",
        ) from exc

    if not result.code:
        raise HTTPException(
            status_code=502,
            detail="Solver returned an empty response. Please try again.",
        )

    return SolveResponse(**result.to_dict())


@app.get("/")
def root():
    """Basic root endpoint, mostly useful for a quick manual sanity check."""
    return {
        "message": "LeetCode AI Assistant backend is running.",
        "solver": solver.__class__.__name__,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
