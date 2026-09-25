from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.deps import require_role, get_current_user
from app.models.models import User
from app.schemas.workout_execution import (
    WorkoutExecutionCreate, WorkoutExecutionUpdate, ExerciseResultUpdate,
    WorkoutExecutionResponse, WorkoutExecutionDetailResponse, ExerciseResultResponse,
)
from app.services import workout_execution_service as wes

router = APIRouter(prefix="/workouts/{workout_id}/executions", tags=["workout-executions"])


def format_execution(e):
    return {
        "id": e.id, "workout_id": e.workout_id, "athlete_id": e.athlete_id,
        "started_at": e.started_at, "finished_at": e.finished_at,
        "status": e.status, "notes": e.notes,
        "created_at": e.created_at, "updated_at": e.updated_at,
    }


def format_execution_detail(e):
    detail = format_execution(e)
    detail["exercise_results"] = [format_result(r) for r in e.exercise_results]
    return detail


def format_result(r):
    return {
        "id": r.id, "workout_exercise_id": r.workout_exercise_id,
        "status": r.status, "actual_sets": r.actual_sets,
        "actual_repetitions": r.actual_repetitions,
        "actual_duration_seconds": r.actual_duration_seconds,
        "actual_distance_meters": r.actual_distance_meters,
        "actual_weight_kg": r.actual_weight_kg,
        "notes": r.notes, "completed_at": r.completed_at,
    }


@router.post("", response_model=WorkoutExecutionDetailResponse, status_code=status.HTTP_201_CREATED)
def start_execution(
    workout_id: int,
    data: WorkoutExecutionCreate,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = current_user.athlete
    if not athlete:
        raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
    try:
        execution = wes.start_execution(db, athlete.id, workout_id, notes=data.notes)
        return format_execution_detail(execution)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[WorkoutExecutionResponse])
def list_executions(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "athlete":
        athlete = current_user.athlete
        if not athlete:
            raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
        executions = wes.list_athlete_executions(db, athlete.id, workout_id)
        return [format_execution(e) for e in executions]
    elif current_user.role == "coach":
        coach = current_user.coach
        if not coach:
            raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
        executions = wes.list_coach_executions(db, coach.id, workout_id)
        return [format_execution(e) for e in executions]
    raise HTTPException(status_code=403, detail="Acesso negado")


@router.get("/{execution_id}", response_model=WorkoutExecutionDetailResponse)
def get_execution(
    workout_id: int,
    execution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        if current_user.role == "athlete":
            athlete = current_user.athlete
            if not athlete:
                raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
            execution = wes.get_execution_athlete(db, execution_id, athlete.id)
        elif current_user.role == "coach":
            coach = current_user.coach
            if not coach:
                raise HTTPException(status_code=404, detail="Perfil de treinador nao encontrado")
            execution = wes.get_execution_coach(db, execution_id, coach.id)
        else:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return format_execution_detail(execution)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{execution_id}", response_model=WorkoutExecutionDetailResponse)
def update_execution(
    workout_id: int,
    execution_id: int,
    data: WorkoutExecutionUpdate,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = current_user.athlete
    if not athlete:
        raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
    try:
        execution = wes.update_execution(
            db, execution_id, athlete.id,
            status=data.status, notes=data.notes, finished_at=data.finished_at,
        )
        return format_execution_detail(execution)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{execution_id}/exercises/{workout_exercise_id}", response_model=ExerciseResultResponse)
def add_exercise_result(
    workout_id: int,
    execution_id: int,
    workout_exercise_id: int,
    data: ExerciseResultUpdate,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    athlete = current_user.athlete
    if not athlete:
        raise HTTPException(status_code=404, detail="Perfil de atleta nao encontrado")
    try:
        result = wes.add_exercise_result(
            db, execution_id, athlete.id, workout_exercise_id,
            status=data.status, actual_sets=data.actual_sets,
            actual_repetitions=data.actual_repetitions,
            actual_duration_seconds=data.actual_duration_seconds,
            actual_distance_meters=data.actual_distance_meters,
            actual_weight_kg=data.actual_weight_kg,
            notes=data.notes,
        )
        return format_result(result)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
