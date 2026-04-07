"""
AI service — HuggingFace zero-shot classification.

Uses facebook/bart-large-mnli to classify report text into
one of the candidate labels passed in (category names from DB).

The HuggingFace pipeline is lazy-loaded to avoid slow imports and
surprise model downloads during test runs.
"""

from __future__ import annotations

import json
import logging
import threading

from transformers import pipeline

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_classifier_lock = threading.Lock()
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is not None:
        return _classifier

    with _classifier_lock:
        if _classifier is None:
            settings = get_settings()
            # Downloads ~1.6 GB on first run, then cached locally by HuggingFace.
            logger.info(
                "Loading HuggingFace classifier model=%s revision=%s device=%s",
                settings.ai_hf_model,
                settings.ai_hf_revision,
                settings.ai_hf_device,
            )
            pipeline_kwargs: dict[str, object] = {
                "model": settings.ai_hf_model,
                "device": settings.ai_hf_device,
            }
            if settings.ai_hf_revision:
                pipeline_kwargs["revision"] = settings.ai_hf_revision

            _classifier = pipeline("zero-shot-classification", **pipeline_kwargs)
    return _classifier


def warmup_model() -> bool:
    """Eagerly load the model (optional). Returns True on success."""
    settings = get_settings()
    if not settings.ai_enabled:
        return False

    try:
        _get_classifier()
        return True
    except Exception:
        logger.exception("AI warmup failed.")
        return False


def _classify_text_openai(text: str, candidate_labels: list[str]) -> str | None:
    """
    OpenAI fallback classifier.

    Requires `OPENAI_API_KEY` to be available in the environment.
    """
    settings = get_settings()
    if not settings.ai_openai_fallback_enabled:
        return None
    if not settings.openai_api_key:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_openai_timeout_seconds)
        response = client.responses.create(
            model=settings.ai_openai_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You classify citizen reports into exactly one category label. "
                        "Return only a JSON object that matches the schema."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Report description:\n{text}\n\n"
                        "Choose the single best label from:\n"
                        + "\n".join(f"- {label}" for label in candidate_labels)
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "report_category",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string", "enum": candidate_labels},
                        },
                        "required": ["label"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )

        parsed = json.loads(response.output_text)
        label = parsed.get("label")
        if isinstance(label, str) and label in candidate_labels:
            return label

        logger.warning("OpenAI fallback returned unexpected label=%r", label)
        return None
    except Exception:
        logger.exception("OpenAI fallback classification failed.")
        return None


def classify_text(
    text: str,
    candidate_labels: list[str],
    *,
    min_confidence: float | None = None,
) -> str | None:
    """
    Classify free-form report text into one of the candidate category names.

    Args:
        text:             The report description submitted by the user.
        candidate_labels: Category names fetched live from the DB.
        min_confidence:   If set, return None when the top score is below this threshold.

    Returns:
        The top predicted category name, or None if classification fails.
    """
    if not text or not candidate_labels:
        logger.warning("classify_text called with empty text or no candidate labels.")
        return None

    settings = get_settings()
    if not settings.ai_enabled:
        return None

    top_label = None
    try:
        classifier = _get_classifier()
        result = classifier(text, candidate_labels)
        # result = {"labels": ["Roads", "Waste", ...], "scores": [0.91, 0.05, ...], ...}
        top_label = result["labels"][0]
        top_score: float = result["scores"][0]
        logger.info("Classified text as '%s' (confidence %.2f)", top_label, top_score)
        if min_confidence is not None and top_score < min_confidence:
            logger.info(
                "Classification below min_confidence (%.2f < %.2f) - trying OpenAI fallback.",
                top_score,
                min_confidence,
            )
            top_label = None
    except Exception:
        logger.exception("HuggingFace classification failed - trying OpenAI fallback.")
        top_label = None

    if top_label is not None:
        return top_label

    return _classify_text_openai(text, candidate_labels)
