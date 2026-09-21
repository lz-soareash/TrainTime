from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Sport
from app.schemas.sport import SportBase, SportDetail

router = APIRouter(prefix="/sports", tags=["sports"])


@router.get("", response_model=list[SportBase])
def list_sports(db: Session = Depends(get_db)):
    return db.query(Sport).all()


@router.get("/{sport_id}", response_model=SportDetail)
def get_sport(sport_id: int, db: Session = Depends(get_db)):
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
    return sport


@router.get("/{sport_id}/positions", response_model=list[dict])
def get_sport_positions(sport_id: int, db: Session = Depends(get_db)):
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
    return [{"id": p.id, "name": p.name, "sport_id": p.sport_id} for p in sport.positions]


@router.get("/{sport_id}/attributes", response_model=list[dict])
def get_sport_attributes(sport_id: int, db: Session = Depends(get_db)):
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise HTTPException(status_code=404, detail="Sport not found")
    return [{"id": a.id, "name": a.name, "sport_id": a.sport_id} for a in sport.attributes]
