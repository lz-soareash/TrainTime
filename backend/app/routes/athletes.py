from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.core.deps import require_role
from app.models.models import User, Athlete, Sport, Position, SportAttribute, AthleteAttribute
from app.schemas.profile import (
    AthleteProfileUpdate, AthleteProfileResponse,
    SportResponse, PositionResponse, AthleteAttributeValue,
)
from app.services import team_service

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.get("/me", response_model=AthleteProfileResponse)
def get_athlete_profile(
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).options(
        joinedload(Athlete.sport),
        joinedload(Athlete.position),
    ).filter(Athlete.user_id == current_user.id).first()

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de atleta nao encontrado",
        )

    return {
        "id": athlete.id,
        "user_id": athlete.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "sport": athlete.sport,
        "position": athlete.position,
        "created_at": current_user.created_at,
    }


@router.put("/me", response_model=AthleteProfileResponse)
def update_athlete_profile(
    data: AthleteProfileUpdate,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de atleta nao encontrado",
        )

    if data.name is not None:
        current_user.name = data.name

    sport_changed = "sport_id" in data.model_fields_set
    position_changed = "position_id" in data.model_fields_set

    if sport_changed:
        if data.sport_id is not None:
            sport = db.query(Sport).filter(Sport.id == data.sport_id).first()
            if not sport:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Esporte invalido",
                )
            athlete.sport_id = data.sport_id
        else:
            athlete.sport_id = None
            athlete.position_id = None

    if position_changed and data.sport_id is not None:
        if athlete.sport_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selecione um esporte antes de definir a posicao",
            )
        position = db.query(Position).filter(
            Position.id == data.position_id,
            Position.sport_id == athlete.sport_id,
        ).first()
        if not position:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Posicao invalida para o esporte selecionado",
            )
        athlete.position_id = data.position_id

    db.commit()
    db.refresh(current_user)
    db.refresh(athlete)

    athlete_full = db.query(Athlete).options(
        joinedload(Athlete.sport),
        joinedload(Athlete.position),
    ).filter(Athlete.user_id == current_user.id).first()

    return {
        "id": athlete_full.id,
        "user_id": athlete_full.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "sport": athlete_full.sport,
        "position": athlete_full.position,
        "created_at": current_user.created_at,
    }


@router.get("/me/attributes", response_model=list[AthleteAttributeValue])
def get_athlete_attributes(
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de atleta nao encontrado",
        )

    attrs = db.query(AthleteAttribute).options(
        joinedload(AthleteAttribute.attribute),
    ).filter(AthleteAttribute.athlete_id == athlete.id).all()

    return [
        {
            "id": a.id,
            "attribute_id": a.attribute_id,
            "attribute_name": a.attribute.name,
            "value": a.value,
        }
        for a in attrs
    ]


@router.put("/me/attributes", response_model=list[AthleteAttributeValue])
def update_athlete_attributes(
    data: dict,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de atleta nao encontrado",
        )
    if not athlete.sport_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selecione um esporte antes de atualizar atributos",
        )

    sport_attrs = db.query(SportAttribute).filter(
        SportAttribute.sport_id == athlete.sport_id
    ).all()
    valid_attr_ids = {a.id for a in sport_attrs}

    attributes = data.get("attributes", [])
    for item in attributes:
        attr_id = item.get("attribute_id")
        value = item.get("value")
        if attr_id not in valid_attr_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Atributo ID {attr_id} nao pertence ao esporte selecionado",
            )
        if not isinstance(value, (int, float)) or value < 0 or value > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Valor do atributo {attr_id} deve ser entre 0 e 100",
            )

    db.query(AthleteAttribute).filter(
        AthleteAttribute.athlete_id == athlete.id
    ).delete()

    for item in attributes:
        attr = AthleteAttribute(
            athlete_id=athlete.id,
            attribute_id=item["attribute_id"],
            value=item["value"],
        )
        db.add(attr)

    db.commit()

    attrs = db.query(AthleteAttribute).options(
        joinedload(AthleteAttribute.attribute),
    ).filter(AthleteAttribute.athlete_id == athlete.id).all()

    return [
        {
            "id": a.id,
            "attribute_id": a.attribute_id,
            "attribute_name": a.attribute.name,
            "value": a.value,
        }
        for a in attrs
    ]


@router.get("/me/teams")
def get_athlete_teams(
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de atleta nao encontrado",
        )
    return team_service.list_athlete_teams(db, athlete.id)


@router.get("/compatible")
def get_compatible_athletes(
    sport_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    athletes = team_service.get_compatible_athletes(db, sport_id, 0)
    return [
        {
            "id": a.id,
            "name": a.user.name if a.user else "Unknown",
            "sport_id": a.sport_id,
            "position_id": a.position_id,
            "position_name": a.position.name if a.position else None,
        }
        for a in athletes
    ]
