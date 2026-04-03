"""
AI service — HuggingFace zero-shot classification.

Uses facebook/bart-large-mnli to classify report text into
one of the candidate labels passed in (category names from DB).
"""

import logging

from transformers import pipeline

logger = logging.getLogger(__name__)

# Loaded once at startup — downloading ~1.6 GB on first run,
# then cached locally by HuggingFace in ~/.cache/huggingface/
_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")


def classify_text(text: str, candidate_labels: list[str]) -> str | None:
    """
    Classify free-form report text into one of the candidate category names.

    Args:
        text:             The report description submitted by the user.
        candidate_labels: Category names fetched live from the DB.

    Returns:
        The top predicted category name, or None if classification fails.
    """
    if not text or not candidate_labels:
        logger.warning("classify_text called with empty text or no candidate labels.")
        return None

    try:
        result = _classifier(text, candidate_labels)
        # result = {"labels": ["Roads", "Waste", ...], "scores": [0.91, 0.05, ...], ...}
        top_label: str = result["labels"][0]
        top_score: float = result["scores"][0]
        logger.info("Classified text as '%s' (confidence %.2f)", top_label, top_score)
        return top_label
    except Exception:
        logger.exception("Classification failed — returning None.")
        return None