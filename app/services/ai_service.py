"""
AI service — HuggingFace zero-shot classification.

Uses facebook/bart-large-mnli to classify report text into
one of the candidate labels passed in (category names from DB).

The HuggingFace pipeline is lazy-loaded to avoid slow imports and
surprise model downloads during test runs.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
import threading
from time import monotonic, perf_counter

from transformers import pipeline

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_classifier_lock = threading.Lock()
_classifier = None

_classification_cache_lock = threading.Lock()
_classification_cache: dict[tuple[str, tuple[str, ...], float | None], "_ClassificationCacheEntry"] = {}


@dataclass(frozen=True)
class _ClassificationCacheEntry:
    label: str
    expires_at_monotonic: float


def _normalize_text_cache_key(text: str) -> str:
    # Keep key reasonably stable across superficial user input differences.
    compacted = re.sub(r"\s+", " ", text).strip()
    return compacted.casefold()


def _classification_cache_get(
    *,
    key: tuple[str, tuple[str, ...], float | None],
    now_monotonic: float,
) -> str | None:
    with _classification_cache_lock:
        entry = _classification_cache.get(key)
        if entry is None:
            return None
        if entry.expires_at_monotonic <= now_monotonic:
            _classification_cache.pop(key, None)
            return None
        return entry.label


def _classification_cache_set(
    *,
    key: tuple[str, tuple[str, ...], float | None],
    label: str,
    ttl_seconds: int,
    now_monotonic: float,
) -> None:
    if ttl_seconds <= 0:
        return
    expires_at = now_monotonic + float(ttl_seconds)
    with _classification_cache_lock:
        _classification_cache[key] = _ClassificationCacheEntry(label=label, expires_at_monotonic=expires_at)


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
    start = perf_counter()
    cache_hit = False
    if not text or not candidate_labels:
        logger.warning("classify_text called with empty text or no candidate labels.")
        return None

    settings = get_settings()
    if not settings.ai_enabled:
        return None

    ttl_seconds = int(getattr(settings, "ai_cache_ttl_seconds", 0) or 0)
    cache_key = (
        _normalize_text_cache_key(text),
        tuple(sorted(candidate_labels, key=str.casefold)),
        float(min_confidence) if min_confidence is not None else None,
    )
    if ttl_seconds > 0:
        cached = _classification_cache_get(key=cache_key, now_monotonic=monotonic())
        if cached is not None:
            cache_hit = True
            elapsed_ms = (perf_counter() - start) * 1000
            logger.info("AI classification latency: %.0fms (cache hit)", elapsed_ms)
            return cached

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
        logger.warning(
            "AI unavailable — skipping HuggingFace classification (trying OpenAI fallback).",
            exc_info=True,
        )
        top_label = None

    if top_label is not None:
        if ttl_seconds > 0 and not cache_hit:
            _classification_cache_set(
                key=cache_key,
                label=top_label,
                ttl_seconds=ttl_seconds,
                now_monotonic=monotonic(),
            )
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("AI classification latency: %.0fms", elapsed_ms)
        return top_label

    label = _classify_text_openai(text, candidate_labels)
    if isinstance(label, str) and label and ttl_seconds > 0 and not cache_hit:
        _classification_cache_set(
            key=cache_key,
            label=label,
            ttl_seconds=ttl_seconds,
            now_monotonic=monotonic(),
        )

    elapsed_ms = (perf_counter() - start) * 1000
    logger.info("AI classification latency: %.0fms", elapsed_ms)
    return label


def generate_confirmation_message(
    description: str,
    *,
    category_label: str | None = None,
    possible_duplicate_of: int | None = None,
) -> str | None:
    """
    Generate a short confirmation message for a newly created report.

    Uses OpenAI when configured; otherwise returns a deterministic template.
    """
    start = perf_counter()
    settings = get_settings()

    template_parts: list[str] = ["Thanks for your report — we’ve received it and will review it shortly."]
    if category_label:
        template_parts.append(f"Initial category: {category_label}.")
    if possible_duplicate_of is not None:
        template_parts.append(f"This may be a duplicate of report #{possible_duplicate_of}; our team will review.")
    template_message = " ".join(template_parts)

    if not settings.ai_enabled:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("AI confirmation generation latency: %.0fms (AI disabled)", elapsed_ms)
        return template_message

    if not settings.openai_api_key or not settings.ai_openai_fallback_enabled:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("AI confirmation generation latency: %.0fms (template)", elapsed_ms)
        return template_message

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key, timeout=settings.ai_openai_timeout_seconds)
        user_bits = [f"Description:\n{description.strip()}"]
        if category_label:
            user_bits.append(f"Category: {category_label}")
        if possible_duplicate_of is not None:
            user_bits.append(f"Possible duplicate of report id: {possible_duplicate_of}")

        response = client.responses.create(
            model=settings.ai_openai_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You write short confirmation messages for a city report app. "
                        "Be concise, friendly, and specific. Do not ask questions."
                    ),
                },
                {"role": "user", "content": "\n".join(user_bits)},
            ],
        )
        message = (response.output_text or "").strip()
        if not message:
            message = template_message

        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("AI confirmation generation latency: %.0fms", elapsed_ms)
        return message
    except Exception:
        logger.warning("AI confirmation generation failed — using template.", exc_info=True)
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("AI confirmation generation latency: %.0fms (template fallback)", elapsed_ms)
        return template_message
