# Smart Citizen Complaint Management System (Backend)

FastAPI backend skeleton for managing citizen reports with **Supabase authentication** (external) and **AI-assisted classification** (placeholder).

This repository contains **structure only**: routers, models, schemas, services, and a mocked Supabase JWT verifier.

## Quickstart (local)

1. Create a virtualenv and install dependencies:
   - `python -m venv .venv`
   - `.\.venv\Scripts\activate`
   - `pip install -r requirements.txt`

2. Configure environment:
   - Copy `.env.example` → `.env`
   - Update `DATABASE_URL` if needed

3. Run the API:
   - `uvicorn app.main:app --reload`

API docs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/api/v1/openapi.json`

## Authentication note (Supabase)

- This project **does not** implement login/registration/JWT issuance.
- Routes expect a **Bearer** token in `Authorization: Bearer <jwt>`.
- Token verification is **mocked** (payload decoding only; no signature verification).

## Project layout

- `app/main.py` - FastAPI app entrypoint
- `app/api/router.py` - API router aggregator
- `app/core/` - config + security placeholder
- `app/db/` - SQLAlchemy base + session
- `app/models/` - SQLAlchemy models
- `app/schemas/` - Pydantic schemas
- `app/routers/` - API endpoints (no business logic)
- `app/services/` - service layer placeholders (AI + reports)
- `app/utils/` - dependencies + helpers

