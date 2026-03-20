"""
AI service placeholder.

This module is intentionally simple so it can be replaced later with:
- OpenAI API calls
- HuggingFace/transformers pipelines
- a self-hosted model service
"""


def classify_text(text: str) -> str:
    """
    Classify free-form report text into a category name.

    Structure-only mock:
    - Always returns "Infrastructure".
    """

    _ = text
    return "Infrastructure"

