from fastapi import APIRouter, Depends

from app.schemas.user import CurrentUser
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=CurrentUser)
def read_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """
    Return the current authenticated user (decoded from Supabase JWT).

    No DB lookup is performed in this template.
    """

    return current_user

