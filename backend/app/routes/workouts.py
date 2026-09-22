from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.core.deps import require_role, get_current_user
from app.models.models import User
from app.schemas.workout import (
    WorkoutCreate, WorkoutUpdate, WorkoutResponse, WorkoutListResponse,
)
from app.services import workout_service

router = APIRouter(prefix="/workouts", tags=["workouts"])


def format_workout_response(workout):
    return {
        "id": workout.id,
        "team_id": workout.team_id,
        "team": {"id": workout.team.id, "name": workout.team.name} if workout.team else None,
        "title": workout.title,
        "description": workout.description,
        "scheduled_at": workout.scheduled_at,
        "duration_minutes": workout.duration_minutes,
        "status": workout.status,
        "created_at": workout.created_at,
        "updated_at": workout.updated_at,
    }


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
def create_workout(
    data: WorkoutCreate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        workout = workout_service.create_workout(
            db, coach.id, data.team_id, data.title,
            data.description, data.scheduled_at, data.duration_minutes,
        )
        return format_workout_response(workout)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[WorkoutListResponse])
def list_workouts(
    team_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "coach":
        coach = current_user.coach
        if not coach:
            raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
        return workout_service.list_coach_workouts(db, coach.id, team_id, status_filter)
    elif current_user.role == "athlete":
        athlete = current_user.athlete
        if not athlete:
            raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
        return workout_service.list_athlete_workouts(db, athlete.id, status_filter)
    else:
        raise HTTPException(status_code=403, detail="Acesso negado")


@router.get("/{workout_id}", response_model=WorkoutResponse)
def get_workout(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        workout = workout_service.get_workout_detail(db, workout_id, current_user.id, current_user.role)
        return format_workout_response(workout)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{workout_id}", response_model=WorkoutResponse)
def update_workout(
    workout_id: int,
    data: WorkoutUpdate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        workout = workout_service.update_workout(
            db, workout_id, coach.id,
            title=data.title,
            description=data.description,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes,
            status=data.status,
        )
        return format_workout_response(workout)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(
    workout_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        workout_service.delete_workout(db, workout_id, coach.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
