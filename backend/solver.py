"""
solver.py
=========
Provider-agnostic solver architecture for the LeetCode AI Assistant.

This module defines an abstract `BaseSolver` interface and a concrete
`MockSolver` implementation. The rest of the application (app.py) only
ever talks to `BaseSolver`, so swapping MockSolver for a real LLM-backed
solver (Gemini, OpenAI, Claude, Ollama, or any REST API) requires NO
changes anywhere else in the codebase -- just point `get_solver()` to a
different class.

Author: Senior Full-Stack AI Engineer
"""


from abc import ABC, abstractmethod
from typing import Dict
import random
import os
import json

from dotenv import load_dotenv
from google import genai

from prompt import build_solver_prompt

load_dotenv()


class SolverResult:
    """
    Simple data container representing the result of a solve operation.
    Keeping this as an explicit class (rather than a raw dict) makes the
    contract between solvers and the API layer explicit and type-safe.
    """

    def __init__(self, code: str, time_complexity: str, space_complexity: str):
        self.code = code
        self.time_complexity = time_complexity
        self.space_complexity = space_complexity

    def to_dict(self) -> Dict[str, str]:
        return {
            "code": self.code,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
        }


class BaseSolver(ABC):
    """
    Abstract base class that defines the interface every solver must
    implement. Any new provider integration (Gemini, OpenAI, Claude,
    Ollama, custom REST API, etc.) should subclass this and implement
    `solve()`.
    """

    @abstractmethod
    def solve(self, title: str, description: str, language: str = "python") -> SolverResult:
        """
        Given a problem title, description, and target language, return
        a SolverResult containing generated code, time complexity, and
        space complexity.

        Args:
            title: The LeetCode problem title.
            description: The full problem description (including
                         examples/constraints if available).
            language: Target programming language for the solution.

        Returns:
            SolverResult
        """
        raise NotImplementedError


class MockSolver(BaseSolver):
    """
    Default, offline solver used for local development and testing.

    This solver does NOT call any external LLM API. It deterministically
    generates a plausible-looking sample solution so the full pipeline
    (extension -> backend -> UI) can be exercised end-to-end without any
    API key or network dependency.

    ------------------------------------------------------------------
    TODO (FUTURE DEVELOPERS): Replace MockSolver with a real provider.
    ------------------------------------------------------------------
    Below are the exact integration points. Because BaseSolver defines
    the contract, you only need to:
        1. Create a new class, e.g. `GeminiSolver(BaseSolver)`,
           `OpenAISolver(BaseSolver)`, `ClaudeSolver(BaseSolver)`, or
           `OllamaSolver(BaseSolver)`.
        2. Implement `solve()` using the provider's SDK/REST API.
        3. Update `get_solver()` at the bottom of this file to return
           an instance of your new class instead of MockSolver.

    Example skeletons (NOT implemented here, per project requirements):

        # TODO: Gemini integration
        # class GeminiSolver(BaseSolver):
        #     def __init__(self, api_key: str):
        #         import google.generativeai as genai
        #         genai.configure(api_key=api_key)
        #         self.model = genai.GenerativeModel("gemini-1.5-pro")
        #
        #     def solve(self, title, description, language="python"):
        #         prompt = build_solver_prompt(title, description, language)
        #         response = self.model.generate_content(prompt)
        #         # TODO: parse response.text into code/time/space complexity
        #         ...

        # TODO: OpenAI integration
        # class OpenAISolver(BaseSolver):
        #     def __init__(self, api_key: str):
        #         from openai import OpenAI
        #         self.client = OpenAI(api_key=api_key)
        #
        #     def solve(self, title, description, language="python"):
        #         prompt = build_solver_prompt(title, description, language)
        #         response = self.client.chat.completions.create(
        #             model="gpt-4o",
        #             messages=[{"role": "user", "content": prompt}],
        #         )
        #         # TODO: parse response.choices[0].message.content
        #         ...

        # TODO: Claude (Anthropic) integration
        # class ClaudeSolver(BaseSolver):
        #     def __init__(self, api_key: str):
        #         import anthropic
        #         self.client = anthropic.Anthropic(api_key=api_key)
        #
        #     def solve(self, title, description, language="python"):
        #         prompt = build_solver_prompt(title, description, language)
        #         response = self.client.messages.create(
        #             model="claude-sonnet-4-6",
        #             max_tokens=1500,
        #             messages=[{"role": "user", "content": prompt}],
        #         )
        #         # TODO: parse response.content into code/time/space complexity
        #         ...

        # TODO: Ollama (local LLM) integration
        # class OllamaSolver(BaseSolver):
        #     def __init__(self, base_url="http://localhost:11434", model="llama3"):
        #         self.base_url = base_url
        #         self.model = model
        #
        #     def solve(self, title, description, language="python"):
        #         import requests
        #         prompt = build_solver_prompt(title, description, language)
        #         resp = requests.post(f"{self.base_url}/api/generate", json={
        #             "model": self.model, "prompt": prompt, "stream": False
        #         })
        #         # TODO: parse resp.json()["response"]
        #         ...

        # TODO: Generic REST API integration
        # class RestApiSolver(BaseSolver):
        #     def __init__(self, endpoint_url: str, api_key: str = None):
        #         self.endpoint_url = endpoint_url
        #         self.api_key = api_key
        #
        #     def solve(self, title, description, language="python"):
        #         import requests
        #         prompt = build_solver_prompt(title, description, language)
        #         headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        #         resp = requests.post(self.endpoint_url, json={"prompt": prompt}, headers=headers)
        #         # TODO: parse resp.json() into code/time/space complexity
        #         ...
    """

class GeminiSolver(BaseSolver):
    """
    Gemini-powered solver implementation.

    This solver uses the Google Gen AI SDK to generate real LeetCode
    solutions while preserving the same SolverResult contract used by
    MockSolver.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        
        print(f"Using Gemini model: {self.model}")

    def solve(
        self,
        title: str,
        description: str,
        language: str = "python"
    ) -> SolverResult:

        # Build the prompt using the shared prompt-building utility.
        prompt = build_solver_prompt(title, description, language)

        # Call Gemini
        try:

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )

            response_text = response.text.strip()

        except Exception as e:
            return SolverResult(
                code=f"Gemini API Error:\n{str(e)}",
                time_complexity="Unknown",
                space_complexity="Unknown",
            )

        # Parse the JSON returned by Gemini
        try:
            data = json.loads(response_text)

            return SolverResult(
                code=data["code"],
                time_complexity=data["time_complexity"],
                space_complexity=data["space_complexity"],
            )

        except (json.JSONDecodeError, KeyError):
            # Gracefully fall back if Gemini returns malformed JSON.
            return SolverResult(
                code=response_text,
                time_complexity="Unknown",
                space_complexity="Unknown",
            )

def get_solver() -> BaseSolver:
    """
    Factory function that returns the solver instance to be used by the
    application.

    TODO (FUTURE DEVELOPERS): To switch providers, change the return
    value below, e.g.:

        return GeminiSolver(api_key=os.getenv("GEMINI_API_KEY"))
        return OpenAISolver(api_key=os.getenv("OPENAI_API_KEY"))
        return ClaudeSolver(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return OllamaSolver()
        return RestApiSolver(endpoint_url=os.getenv("SOLVER_API_URL"))

    No other file in this project needs to change.
    """
    return GeminiSolver()
