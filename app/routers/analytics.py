from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.analytics_service import get_summary
from app.schemas.user import CurrentUser
from app.api.deps import get_current_user  # ако веќе го имаш

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # 🔒 Only officer/admin
    if current_user.role not in ["officer", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return get_summary(db)