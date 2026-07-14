"""
prompt.py
=========
Centralized prompt-construction utilities.

Keeping prompt engineering in a single module means that when a real LLM
provider is wired up in solver.py, the prompt format only needs to be
maintained in ONE place, regardless of which provider is used.
"""


def build_solver_prompt(title: str, description: str, language: str = "python") -> str:
    return f"""
You are an expert competitive programmer.

Solve the following LeetCode problem.

Title:
{title}

Problem Description:
{description}

Write the solution in {language}.

Return ONLY a valid JSON object.

The JSON MUST have exactly these fields:

{{
  "code": "<complete {language} solution>",
  "time_complexity": "<Big-O time complexity>",
  "space_complexity": "<Big-O space complexity>"
}}

Rules:
- Return only JSON.
- Do not wrap the JSON in Markdown.
- Do not use triple backticks.
- Do not include explanations.
- Do not include comments outside the code.
- The value of "code" must be a complete solution.
- The response must be a single valid JSON object.
"""

def build_parsing_instructions() -> str:
    """
    Returns a short reusable snippet describing the expected response
    format. Useful when a future provider needs response-format
    reinforcement (e.g., for models prone to ignoring formatting rules).
    """
    return (
        "Respond ONLY in the CODE / TIME_COMPLEXITY / SPACE_COMPLEXITY "
        "format described above. Do not add any extra commentary."
    )
