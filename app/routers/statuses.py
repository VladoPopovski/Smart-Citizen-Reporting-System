from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.status import Status

router = APIRouter(prefix="/statuses", tags=["Statuses"])

@router.get("/")
def get_statuses(db: Session = Depends(get_db)):
    return db.query(Status).all()