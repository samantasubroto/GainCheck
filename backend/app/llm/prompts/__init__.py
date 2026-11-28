"""The text of the prompts lives in .txt files next to this file, so they are easy to read and edit."""

from pathlib import Path

PROMPT_FOLDER = Path(__file__).parent


def load_prompt(name):
    """Read the prompt file called name.txt and return its text."""
    return (PROMPT_FOLDER / (name + ".txt")).read_text(encoding="utf-8")
