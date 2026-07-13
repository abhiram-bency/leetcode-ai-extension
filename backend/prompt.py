"""
prompt.py
=========
Centralized prompt-construction utilities.

Keeping prompt engineering in a single module means that when a real LLM
provider is wired up in solver.py, the prompt format only needs to be
maintained in ONE place, regardless of which provider is used.
"""


def build_solver_prompt(title: str, description: str, language: str = "python") -> str:
    """
    Build a structured prompt instructing an LLM to solve a LeetCode-style
    problem and return code + complexity analysis.

    This function is provider-agnostic: it just returns a string. Any
    future solver (Gemini/OpenAI/Claude/Ollama/REST) can feed this string
    directly into its respective chat/completions API.

    Args:
        title: The problem title.
        description: The full problem description, including examples
                      and constraints if present.
        language: Target programming language for the generated solution.

    Returns:
        A formatted prompt string.
    """
    safe_title = (title or "Untitled Problem").strip()
    safe_description = (description or "No description provided.").strip()
    safe_language = (language or "python").strip()

    prompt = f"""You are an expert competitive programmer and software engineer.

Solve the following LeetCode problem in {safe_language}.

Problem Title:
{safe_title}

Problem Description:
{safe_description}

Instructions:
1. Provide a complete, correct, and efficient solution in {safe_language}.
2. Include brief inline comments explaining key steps.
3. After the code, clearly state:
   - Time Complexity (Big-O)
   - Space Complexity (Big-O)
4. Do not include unrelated explanation outside of code + complexity.

Respond in the following strict format:

CODE:
<code here>

TIME_COMPLEXITY:
<time complexity here>

SPACE_COMPLEXITY:
<space complexity here>
"""
    return prompt


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
