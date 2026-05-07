from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.status import Status

RESOLVED_STATUS_NAMES = {
    "resolved",
    "closed",
    "resen",
    "reshen",
    "решен",
    "решена",
    "решено",
    "решени",
    "затворен",
    "затворена",
    "затворено",
    "затворени",
}

ACTIVE_STATUS_NAMES = {
    "active",
    "aktiven",
    "aktivna",
    "aktivni",
    "активен",
    "активна",
    "активно",
    "активни",
    "submitted",
    "in progress",
    "pending",
    "нов",
    "нова",
    "поднесен",
    "поднесена",
    "во тек",
    "на чекање",
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
