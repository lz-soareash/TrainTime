from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.core.deps import require_role, get_current_user
from app.models.models import User
from app.schemas.exercise import (
    ExerciseCreate, ExerciseUpdate, ExerciseResponse, ExerciseListResponse,
)
from app.services import exercise_service

router = APIRouter(prefix="/exercises", tags=["exercises"])


def format_exercise_response(exercise):
    return {
        "id": exercise.id,
        "name": exercise.name,
        "description": exercise.description,
        "sport_id": exercise.sport_id,
        "sport": {"id": exercise.sport.id, "name": exercise.sport.name, "icon": exercise.sport.icon} if exercise.sport else None,
        "exercise_type": exercise.exercise_type,
        "created_by": exercise.created_by,
        "created_at": exercise.created_at,
        "updated_at": exercise.updated_at,
    }


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
    data: ExerciseCreate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        exercise = exercise_service.create_exercise(
            db, coach.id, data.name, data.description,
            data.sport_id, data.exercise_type,
        )
        return format_exercise_response(exercise)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ExerciseListResponse])
def list_exercises(
    sport_id: Optional[int] = Query(None),
    exercise_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return exercise_service.list_exercises(db, sport_id, exercise_type)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exercise = exercise_service.get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercicio nao encontrado")
    return format_exercise_response(exercise)


@router.put("/{exercise_id}", response_model=ExerciseResponse)
def update_exercise(
    exercise_id: int,
    data: ExerciseUpdate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        exercise = exercise_service.update_exercise(
            db, exercise_id, coach.id,
            name=data.name, description=data.description,
            exercise_type=data.exercise_type,
        )
        return format_exercise_response(exercise)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        exercise_service.delete_exercise(db, exercise_id, coach.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
