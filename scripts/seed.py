"""
Seed script — creates all tables and inserts development data.

Usage:
    python scripts/seed.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

# Make sure the project root is on the path when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select  # noqa: E402

from app.db.base import Base  # noqa: E402 — imports all models
from app.db.session import engine, SessionLocal  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

CITIZEN_ID = UUID("12345678-1234-1234-1234-123456789012")
OFFICER_ID  = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
ADMIN_ID    = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

USERS = [
    User(id=CITIZEN_ID, email="citizen@example.com", role=UserRole.citizen),
    User(id=OFFICER_ID,  email="officer@example.com",  role=UserRole.officer),
    User(id=ADMIN_ID,    email="admin@example.com",    role=UserRole.admin),
]

REPORTS = [
    Report(
        description="Pothole on Main Street near the bus stop.",
        user_id=CITIZEN_ID,
        latitude=41.9981,
        longitude=21.4254,
    ),
    Report(
        description="Broken street light on Oak Avenue.",
        user_id=CITIZEN_ID,
        latitude=41.9975,
        longitude=21.4261,
    ),
    Report(
        description="Graffiti on the wall of the community centre.",
        user_id=OFFICER_ID,
        latitude=41.9990,
        longitude=21.4270,
    ),
]


def seed() -> None:
    print("Creating tables...")
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        existing_users = {u.id for u in db.scalars(select(User)).all()}

        new_users = [u for u in USERS if u.id not in existing_users]
        if new_users:
            db.add_all(new_users)
            db.commit()
            print(f"Inserted {len(new_users)} user(s).")
        else:
            print("Users already seeded, skipping.")

        if db.scalar(select(func.count()).select_from(Report)) == 0:
            db.add_all(REPORTS)
            db.commit()
            print(f"Inserted {len(REPORTS)} report(s).")
        else:
            print("Reports already seeded, skipping.")

    print("Done.")


if __name__ == "__main__":
    seed()
