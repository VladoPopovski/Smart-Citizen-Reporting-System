from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.category import Category

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()