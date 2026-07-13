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

from prompt import build_solver_prompt


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

    def solve(self, title: str, description: str, language: str = "python") -> SolverResult:
        # Build the prompt using the shared prompt-building utility.
        # In MockSolver we don't actually send this anywhere, but we
        # construct it to demonstrate where a real solver would use it.
        _ = build_solver_prompt(title, description, language)

        sample_code = self._generate_sample_code(title, language)
        time_complexity = self._pick_time_complexity()
        space_complexity = self._pick_space_complexity()

        return SolverResult(
            code=sample_code,
            time_complexity=time_complexity,
            space_complexity=space_complexity,
        )

    @staticmethod
    def _generate_sample_code(title: str, language: str) -> str:
        """Generate a deterministic sample solution for demo purposes."""
        safe_title = (title or "Unknown Problem").strip()

        if language.lower() == "python":
            return f'''# Sample generated solution for: {safe_title}
# NOTE: This is a MOCK solution generated without any real LLM.
# Replace MockSolver in solver.py with a real provider to get
# genuine problem-specific solutions.

def solve(nums, target=None):
    """
    Mock solution template.
    Uses a hash-map based approach as a generic placeholder pattern
    commonly seen in array/two-sum style LeetCode problems.
    """
    seen = {{}}
    for index, value in enumerate(nums):
        complement = target - value if target is not None else 0
        if complement in seen:
            return [seen[complement], index]
        seen[value] = index
    return []


if __name__ == "__main__":
    print(solve([2, 7, 11, 15], 9))
'''
        elif language.lower() in ("javascript", "js"):
            return f'''// Sample generated solution for: {safe_title}
// NOTE: This is a MOCK solution generated without any real LLM.

function solve(nums, target) {{
  const seen = new Map();
  for (let i = 0; i < nums.length; i++) {{
    const complement = target - nums[i];
    if (seen.has(complement)) {{
      return [seen.get(complement), i];
    }}
    seen.set(nums[i], i);
  }}
  return [];
}}

console.log(solve([2, 7, 11, 15], 9));
'''
        elif language.lower() in ("java",):
            return f'''// Sample generated solution for: {safe_title}
// NOTE: This is a MOCK solution generated without any real LLM.

import java.util.HashMap;
import java.util.Map;

class Solution {{
    public int[] solve(int[] nums, int target) {{
        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {{
            int complement = target - nums[i];
            if (seen.containsKey(complement)) {{
                return new int[] {{ seen.get(complement), i }};
            }}
            seen.put(nums[i], i);
        }}
        return new int[] {{}};
    }}
}}
'''
        elif language.lower() in ("cpp", "c++"):
            return f'''// Sample generated solution for: {safe_title}
// NOTE: This is a MOCK solution generated without any real LLM.

#include <vector>
#include <unordered_map>
using namespace std;

class Solution {{
public:
    vector<int> solve(vector<int>& nums, int target) {{
        unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); i++) {{
            int complement = target - nums[i];
            if (seen.count(complement)) {{
                return {{ seen[complement], i }};
            }}
            seen[nums[i]] = i;
        }}
        return {{}};
    }}
}};
'''
        else:
            return f"// Mock solution for '{safe_title}' -- language '{language}' not specifically templated."

    @staticmethod
    def _pick_time_complexity() -> str:
        # Deterministic-ish "sample" complexity, kept simple for the mock.
        return "O(n)"

    @staticmethod
    def _pick_space_complexity() -> str:
        return "O(n)"


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
    return MockSolver()
