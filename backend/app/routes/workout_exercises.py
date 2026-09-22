from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.deps import require_role, get_current_user
from app.models.models import User
from app.schemas.workout_exercise import (
    WorkoutExerciseCreate, WorkoutExerciseUpdate, WorkoutExerciseResponse,
)
from app.services import workout_exercise_service

router = APIRouter(prefix="/workouts/{workout_id}/exercises", tags=["workout-exercises"])


def format_we_response(we):
    return {
        "id": we.id,
        "workout_id": we.workout_id,
        "exercise_id": we.exercise_id,
        "exercise": {"id": we.exercise.id, "name": we.exercise.name, "exercise_type": we.exercise.exercise_type} if we.exercise else None,
        "order": we.order,
        "sets": we.sets,
        "repetitions": we.repetitions,
        "duration_seconds": we.duration_seconds,
        "distance_meters": we.distance_meters,
        "rest_seconds": we.rest_seconds,
        "notes": we.notes,
        "created_at": we.created_at,
        "updated_at": we.updated_at,
    }


@router.post("", response_model=WorkoutExerciseResponse, status_code=status.HTTP_201_CREATED)
def add_exercise(
    workout_id: int,
    data: WorkoutExerciseCreate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        we = workout_exercise_service.add_exercise_to_workout(
            db, workout_id, coach.id, data.exercise_id, data.order,
            sets=data.sets, repetitions=data.repetitions,
            duration_seconds=data.duration_seconds,
            distance_meters=data.distance_meters,
            rest_seconds=data.rest_seconds, notes=data.notes,
        )
        return format_we_response(we)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[WorkoutExerciseResponse])
def list_exercises(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        wes = workout_exercise_service.list_workout_exercises(
            db, workout_id, current_user.id, current_user.role,
        )
        return [format_we_response(we) for we in wes]
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{workout_exercise_id}", response_model=WorkoutExerciseResponse)
def update_exercise(
    workout_id: int,
    workout_exercise_id: int,
    data: WorkoutExerciseUpdate,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        we = workout_exercise_service.update_workout_exercise(
            db, workout_id, workout_exercise_id, coach.id,
            order=data.order, sets=data.sets, repetitions=data.repetitions,
            duration_seconds=data.duration_seconds,
            distance_meters=data.distance_meters,
            rest_seconds=data.rest_seconds, notes=data.notes,
        )
        return format_we_response(we)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{workout_exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    workout_id: int,
    workout_exercise_id: int,
    current_user: User = Depends(require_role("coach")),
    db: Session = Depends(get_db),
):
    coach = current_user.coach
    if not coach:
        raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
    try:
        workout_exercise_service.delete_workout_exercise(db, workout_id, workout_exercise_id, coach.id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
