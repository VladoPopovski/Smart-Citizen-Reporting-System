from __future__ import annotations

import base64
import json
from typing import Any

from fastapi import HTTPException, status

from app.core.config import get_settings


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """
    Decode a JWT payload without verifying the signature.

    IMPORTANT: This is a scaffold for local development only.
    For production, verify signatures with Supabase JWKS.
    """

    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token is not a JWT (expected 3 dot-separated parts).")

    payload_b64 = parts[1]
    payload_bytes = _b64url_decode(payload_b64)
    payload = json.loads(payload_bytes.decode("utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Invalid JWT payload.")

    return payload


def verify_supabase_token(token: str) -> dict[str, Any]:
    """
    Placeholder Supabase JWT verification.

    - Accepts a JWT token issued by Supabase (expected).
    - Currently performs *only* payload decoding and basic shape checks.

    Replace this with real signature verification (JWKS) before production use.
    """

    settings = get_settings()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    if not settings.supabase_mock_verify:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Real Supabase JWT verification is not implemented in this template.",
        )

    try:
        payload = decode_jwt_payload(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )

    # Minimal checks that the payload looks like an auth token.
    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (missing `sub`).",
        )

    return payload

