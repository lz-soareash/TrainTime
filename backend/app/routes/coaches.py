from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.core.deps import require_role
from app.models.models import User, Coach, CoachSport, Sport
from app.schemas.profile import CoachProfileUpdate, CoachProfileResponse, SportResponse

router = APIRouter(prefix="/coaches", tags=["coaches"])


@router.get("/me", response_model=CoachProfileResponse)
def get_coach_profile(
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = db.query(Coach).options(
        joinedload(Coach.sports).joinedload(CoachSport.sport),
    ).filter(Coach.user_id == current_user.id).first()

    if not coach:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de treinador nao encontrado",
        )

    sports_list = [cs.sport for cs in coach.sports]

    return {
        "id": coach.id,
        "user_id": coach.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "sports": sports_list,
        "created_at": current_user.created_at,
    }


@router.put("/me", response_model=CoachProfileResponse)
def update_coach_profile(
    data: CoachProfileUpdate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = db.query(Coach).filter(Coach.user_id == current_user.id).first()
    if not coach:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de treinador nao encontrado",
        )

    if data.name is not None:
        current_user.name = data.name

    if data.sport_ids is not None:
        for sport_id in data.sport_ids:
            sport = db.query(Sport).filter(Sport.id == sport_id).first()
            if not sport:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Esporte ID {sport_id} invalido",
                )

        db.query(CoachSport).filter(CoachSport.coach_id == coach.id).delete()
        for sport_id in data.sport_ids:
            cs = CoachSport(coach_id=coach.id, sport_id=sport_id)
            db.add(cs)

    db.commit()
    db.refresh(current_user)

    coach_full = db.query(Coach).options(
        joinedload(Coach.sports).joinedload(CoachSport.sport),
    ).filter(Coach.user_id == current_user.id).first()

    sports_list = [cs.sport for cs in coach_full.sports]

    return {
        "id": coach_full.id,
        "user_id": coach_full.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "sports": sports_list,
        "created_at": current_user.created_at,
    }
