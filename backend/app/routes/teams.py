from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.deps import require_role, get_current_user
from app.models.models import User
from app.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse, AthleteBasic,
)
from app.services import team_service

router = APIRouter(prefix="/teams", tags=["teams"])


def format_team_response(team):
    athletes = []
    for a in team.athletes:
        athletes.append({
            "id": a.id,
            "name": a.user.name if a.user else "Unknown",
            "sport_id": a.sport_id,
            "position_id": a.position_id,
            "position_name": a.position.name if a.position else None,
        })
    return {
        "id": team.id,
        "name": team.name,
        "sport": {"id": team.sport.id, "name": team.sport.name, "icon": team.sport.icon} if team.sport else None,
        "coach": {"id": team.coach.id, "name": team.coach.user.name} if team.coach and team.coach.user else None,
        "athletes": athletes,
        "created_at": team.created_at,
    }


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        team = team_service.create_team(db, coach.id, data.name, data.sport_id)
        return format_team_response(team)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[TeamListResponse])
def list_teams(
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    return team_service.list_coach_teams(db, coach.id)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = team_service.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipe nao encontrada")

    if current_user.role == "coach":
        if team.coach_id != current_user.coach.id:
            raise HTTPException(status_code=403, detail="Acesso negado")
    elif current_user.role == "athlete":
        athlete = current_user.athlete
        if not athlete:
            raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
        athlete_ids = [a.id for a in team.athletes]
        if athlete.id not in athlete_ids:
            raise HTTPException(status_code=403, detail="Acesso negado")

    return format_team_response(team)


@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        team = team_service.update_team(db, team_id, coach.id, data.name)
        return format_team_response(team)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        team_service.delete_team(db, team_id, coach.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{team_id}/athletes", response_model=list[AthleteBasic])
def list_team_athletes(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = team_service.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipe nao encontrada")

    if current_user.role == "coach":
        if team.coach_id != current_user.coach.id:
            raise HTTPException(status_code=403, detail="Acesso negado")
    elif current_user.role == "athlete":
        athlete = current_user.athlete
        if not athlete:
            raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
        athlete_ids = [a.id for a in team.athletes]
        if athlete.id not in athlete_ids:
            raise HTTPException(status_code=403, detail="Acesso negado")

    return [
        {
            "id": a.id,
            "name": a.user.name if a.user else "Unknown",
            "sport_id": a.sport_id,
            "position_id": a.position_id,
            "position_name": a.position.name if a.position else None,
        }
        for a in team.athletes
    ]


@router.post("/{team_id}/athletes/{athlete_id}", response_model=TeamResponse)
def add_athlete(
    team_id: int,
    athlete_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        team = team_service.add_athlete_to_team(db, team_id, athlete_id, coach.id)
        return format_team_response(team)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        detail = str(e)
        code = 409 if "ja esta" in detail else 400
        raise HTTPException(status_code=code, detail=detail)


@router.delete("/{team_id}/athletes/{athlete_id}", response_model=TeamResponse)
def remove_athlete(
    team_id: int,
    athlete_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        team = team_service.remove_athlete_from_team(db, team_id, athlete_id, coach.id)
        return format_team_response(team)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
