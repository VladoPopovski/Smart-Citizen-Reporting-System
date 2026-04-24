# Smart Citizen Complaint Management System (Backend)

FastAPI backend for managing citizen reports with **Supabase authentication** and **AI-assisted classification** (stub).

## Quickstart

### 1. Start the database

```bash
docker compose up -d
```

This starts a PostgreSQL 18 container on `localhost:5432`.

### 2. Set up the environment

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # Unix

pip install -r requirements.txt
cp .env.example .env
```

The default `.env.example` already points to the Docker database — no changes needed for local dev.

### 3. Create tables and seed data

```bash
python scripts/seed.py
```

Inserts three users and sample reports. Safe to run multiple times (skips existing data).

| Email | Role | UUID |
|---|---|---|
| citizen@example.com | citizen | `12345678-1234-1234-1234-123456789012` |
| officer@example.com | officer | `aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa` |
| admin@example.com | admin | `bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb` |

### 4. Run the API

```bash
fastapi dev
```

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`
- OpenAPI JSON: `http://127.0.0.1:8000/api/v1/openapi.json`

### 5. Run tests

```bash
pytest tests/ -v
```

---

## Authentication

Routes expect `Authorization: Bearer <supabase-jwt>`. In dev mode you can skip this entirely:

**Option A — skip auth** (add to `.env`):
```
DEV_SKIP_AUTH=true
```
Every request is treated as the admin user. Remove before deploying.

**Option B — use a fake JWT** in Swagger's Authorize dialog:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTEyMzQtMTIzNC0xMjM0NTY3ODkwMTIiLCJlbWFpbCI6ImNpdGl6ZW5AZXhhbXBsZS5jb20iLCJhcHBfcm9sZSI6ImNpdGl6ZW4ifQ.signature
```
Signature is ignored in dev (`SUPABASE_MOCK_VERIFY=true`).

---

## Project layout

```
app/
├── main.py              # FastAPI entrypoint
├── api/router.py        # Aggregates all routers
├── core/                # Config + JWT security
├── db/                  # SQLAlchemy base, session, base_class
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response schemas
├── routers/             # Route handlers (no business logic)
├── services/            # Business logic layer
└── utils/               # Auth dependencies + helpers
scripts/
└── seed.py              # Creates tables and inserts dev data
tests/
└── test_report_service.py
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/smart_citizen` | PostgreSQL connection string |
| `SUPABASE_MOCK_VERIFY` | `true` | Skip JWT signature check (dev only) |
| `DEV_SKIP_AUTH` | `false` | Bypass auth entirely, use hardcoded admin user |
| `PROJECT_NAME` | `Smart Citizen Complaint Management System` | Shown in OpenAPI docs |
| `API_V1_STR` | `/api/v1` | API prefix |