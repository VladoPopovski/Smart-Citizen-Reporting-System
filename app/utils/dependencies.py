from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import verify_supabase_token
from app.schemas.user import CurrentUser, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


DEV_USER = CurrentUser(
    id=UUID("12345678-1234-1234-1234-123456789012"),
    email="dev@example.com",
    role=UserRole.admin,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """
    Extract and verify the current user from a Supabase-issued JWT.

    IMPORTANT:
    - This template only decodes JWT payloads (no signature validation).
    - Replace `verify_supabase_token` implementation for production.
    """

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    token = credentials.credentials
    payload = verify_supabase_token(token)

    # Supabase typically uses `sub` as the user id (UUID).
    try:
        user_id = UUID(str(payload["sub"]))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload (`sub` must be a UUID).",
        )

    email = payload.get("email")

    # Your app role might live in custom claims (e.g. `app_role`) or user metadata.
    # This template falls back to "citizen" if missing.
    raw_role = payload.get("app_role") or payload.get("role") or UserRole.citizen.value
    try:
        role = UserRole(str(raw_role))
    except Exception:
        role = UserRole.citizen

    return CurrentUser(id=user_id, email=email, role=role)


def require_roles(*allowed_roles: UserRole):
    """
    Dependency factory for simple role-based access control.

    Example:
      `current_user = Depends(require_roles(UserRole.admin))`
    """

    def _role_dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
        return current_user

    return _role_dependency

