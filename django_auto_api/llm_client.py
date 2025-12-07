# django_auto_api/llm_client.py
import os
from openai import OpenAI


class OpenAIConfigError(RuntimeError):
    pass


# 👇 Option 1: paste your key here for local testing
# Example: API_KEY = "sk-xxxx..."
API_KEY = ""


def _get_api_key() -> str:
    """
    Try environment variable first, then fallback to hardcoded API_KEY.
    Raise a clear error if still empty.
    """
    key_from_env = os.getenv("OPENAI_API_KEY")
    key = key_from_env or API_KEY

    if not key:
        raise OpenAIConfigError(
            "No OpenAI API key configured.\n\n"
            "Either:\n"
            "  1) Set environment variable OPENAI_API_KEY, or\n"
            "  2) Paste your key into django_auto_api/llm_client.py in API_KEY.\n"
        )
    return key


def _get_client() -> OpenAI:
    key = _get_api_key()
    return OpenAI(api_key=key)


def generate_code(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Send a prompt to OpenAI and return the generated code as plain text.
    We assume the prompt instructs the model to output ONLY Python code.
    """
    client = _get_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant that writes clean, valid Python code for "
                    "Django REST Framework. "
                    "Always output ONLY Python code. No explanations, no markdown."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content or ""
