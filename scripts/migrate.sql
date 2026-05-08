-- Idempotent schema patches for prod.
-- Run against the Supabase **direct** Postgres URI (port 5432) BEFORE deploying
-- a new image, since the app has no migration tooling (alembic, etc.).
--
-- Each statement uses IF NOT EXISTS / IF EXISTS so re-runs are safe.
--
-- Usage:
--   psql "$DATABASE_URL_DIRECT" -f scripts/migrate.sql
-- or paste into the Supabase SQL editor.

-- 2026-05 — added by the deployment merge.
-- app/models/user.py now declares email_notifications NOT NULL DEFAULT TRUE.
-- Without this column the upsert_user / settings PATCH paths 500.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email_notifications BOOLEAN NOT NULL DEFAULT TRUE;
