from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.status import Status

RESOLVED_STATUS_NAMES = {
    "resolved",
    "closed",
    "resen",
    "reshen",
    "Ñ€ÐµÑˆÐµÐ½",
    "Ñ€ÐµÑˆÐµÐ½Ð°",
    "Ñ€ÐµÑˆÐµÐ½Ð¾",
    "Ñ€ÐµÑˆÐµÐ½Ð¸",
    "Ð·Ð°Ñ‚Ð²Ð¾Ñ€ÐµÐ½",
    "Ð·Ð°Ñ‚Ð²Ð¾Ñ€ÐµÐ½Ð°",
    "Ð·Ð°Ñ‚Ð²Ð¾Ñ€ÐµÐ½Ð¾",
    "Ð·Ð°Ñ‚Ð²Ð¾Ñ€ÐµÐ½Ð¸",
}

ACTIVE_STATUS_NAMES = {
    "active",
    "aktiven",
    "aktivna",
    "aktivni",
    "Ð°ÐºÑ‚Ð¸Ð²ÐµÐ½",
    "Ð°ÐºÑ‚Ð¸Ð²Ð½Ð°",
    "Ð°ÐºÑ‚Ð¸Ð²Ð½Ð¾",
    "Ð°ÐºÑ‚Ð¸Ð²Ð½Ð¸",
    "submitted",
    "in progress",
    "pending",
    "Ð½Ð¾Ð²",
    "Ð½Ð¾Ð²Ð°",
    "Ð¿Ð¾Ð´Ð½ÐµÑÐµÐ½",
    "Ð¿Ð¾Ð´Ð½ÐµÑÐµÐ½Ð°",
    "Ð²Ð¾ Ñ‚ÐµÐº",
    "Ð½Ð° Ñ‡ÐµÐºÐ°ÑšÐµ",
}


def normalized_status_name(name: str) -> str:
    return " ".join(name.strip().casefold().replace("_", " ").replace("-", " ").split())


def status_ids_for_names(db: Session, names: set[str]) -> list[int]:
    normalized_names = {normalized_status_name(name) for name in names}
    statuses = db.scalars(select(Status)).all()
    return [
        status.id
        for status in statuses
        if isinstance(getattr(status, "name", None), str)
        and normalized_status_name(status.name) in normalized_names
    ]
