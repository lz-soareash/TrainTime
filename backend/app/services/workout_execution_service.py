from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.models import (
    Workout, WorkoutExecution, WorkoutExercise, WorkoutExerciseExecution,
    Athlete, Team, TeamAthlete, PerformanceRecord,
)


def _get_athlete(db: Session, user_id: int) -> Athlete:
    athlete = db.query(Athlete).options(
        joinedload(Athlete.user),
    ).filter(Athlete.user_id == user_id).first()
    if not athlete:
        raise LookupError("Perfil de atleta nao encontrado")
    return athlete


def _get_full(db: Session, execution_id: int) -> WorkoutExecution | None:
    return db.query(WorkoutExecution).options(
        joinedload(WorkoutExecution.workout).joinedload(Workout.team),
        joinedload(WorkoutExecution.athlete).joinedload(Athlete.user),
        joinedload(WorkoutExecution.exercise_results).joinedload(
            WorkoutExerciseExecution.workout_exercise,
        ),
    ).filter(WorkoutExecution.id == execution_id).first()


def _verify_athlete_owns(db: Session, execution_id: int,
                         athlete_id: int) -> WorkoutExecution:
    execution = _get_full(db, execution_id)
    if not execution:
        raise LookupError("Execucao nao encontrada")
    if execution.athlete_id != athlete_id:
        raise PermissionError("Acesso negado")
    return execution


def start_execution(db: Session, athlete_id: int, workout_id: int,
                    notes: str | None = None) -> WorkoutExecution:
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise LookupError("Treino nao encontrado")

    is_member = db.query(TeamAthlete).filter(
        TeamAthlete.team_id == workout.team_id,
        TeamAthlete.athlete_id == athlete_id,
    ).first()
    if not is_member:
        raise PermissionError("Acesso negado")

    active = db.query(WorkoutExecution).filter(
        WorkoutExecution.workout_id == workout_id,
        WorkoutExecution.athlete_id == athlete_id,
        WorkoutExecution.status == "in_progress",
    ).first()
    if active:
        raise ValueError("Ja existe uma execucao em andamento")

    execution = WorkoutExecution(
        workout_id=workout_id,
        athlete_id=athlete_id,
        started_at=datetime.now(timezone.utc),
        status="in_progress",
        notes=notes,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return _get_full(db, execution.id)


def update_execution(db: Session, execution_id: int, athlete_id: int,
                     status: str | None = None, notes: str | None = None,
                     finished_at: datetime | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id)
    if status is not None:
        if status not in ("in_progress", "completed", "cancelled"):
            raise ValueError(f"Status invalido: {status}")
        execution.status = status
    if notes is not None:
        execution.notes = notes
    if finished_at is not None:
        execution.finished_at = finished_at
    if status == "completed" and execution.finished_at is None:
        execution.finished_at = datetime.now(timezone.utc)
    if status == "completed":
        _generate_performance(db, execution)
    db.commit()
    return _get_full(db, execution.id)


def complete_execution(db: Session, execution_id: int, athlete_id: int,
                       notes: str | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id)
    if execution.status == "completed":
        raise ValueError("Execucao ja concluida")
    execution.status = "completed"
    execution.finished_at = datetime.now(timezone.utc)
    if notes is not None:
        execution.notes = notes
    _generate_performance(db, execution)
    db.commit()
    return _get_full(db, execution.id)


def cancel_execution(db: Session, execution_id: int, athlete_id: int,
                     notes: str | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id)
    execution.status = "cancelled"
    if notes is not None:
        execution.notes = notes
    db.commit()
    return _get_full(db, execution.id)


def list_athlete_executions(db: Session, athlete_id: int,
                            workout_id: int | None = None) -> list[WorkoutExecution]:
    query = db.query(WorkoutExecution).options(
        joinedload(WorkoutExecution.workout).joinedload(Workout.team),
        joinedload(WorkoutExecution.athlete).joinedload(Athlete.user),
    ).filter(WorkoutExecution.athlete_id == athlete_id)
    if workout_id is not None:
        query = query.filter(WorkoutExecution.workout_id == workout_id)
    return query.order_by(WorkoutExecution.started_at.desc()).all()


def list_coach_executions(db: Session, coach_id: int,
                          team_id: int | None = None,
                          workout_id: int | None = None) -> list[WorkoutExecution]:
    query = db.query(WorkoutExecution).options(
        joinedload(WorkoutExecution.workout).joinedload(Workout.team),
        joinedload(WorkoutExecution.athlete).joinedload(Athlete.user),
    ).join(Workout).join(Team).filter(Team.coach_id == coach_id)
    if team_id is not None:
        query = query.filter(Workout.team_id == team_id)
    if workout_id is not None:
        query = query.filter(WorkoutExecution.workout_id == workout_id)
    return query.order_by(WorkoutExecution.started_at.desc()).all()


def get_execution_athlete(db: Session, execution_id: int,
                          athlete_id: int) -> WorkoutExecution:
    return _verify_athlete_owns(db, execution_id, athlete_id)


def get_execution_coach(db: Session, execution_id: int,
                        coach_id: int) -> WorkoutExecution:
    execution = _get_full(db, execution_id)
    if not execution:
        raise LookupError("Execucao nao encontrada")
    team = execution.workout.team
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")
    return execution


def add_exercise_result(db: Session, execution_id: int, athlete_id: int,
                        workout_exercise_id: int,
                        status="done", actual_sets=None, actual_repetitions=None,
                        actual_duration_seconds=None, actual_distance_meters=None,
                        actual_weight_kg=None, notes=None) -> WorkoutExerciseExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id)

    we = db.query(WorkoutExercise).filter(
        WorkoutExercise.id == workout_exercise_id,
        WorkoutExercise.workout_id == execution.workout_id,
    ).first()
    if not we:
        raise LookupError("Exercicio do treino nao encontrado")

    result = WorkoutExerciseExecution(
        execution_id=execution_id,
        workout_exercise_id=workout_exercise_id,
        status=status,
        actual_sets=actual_sets,
        actual_repetitions=actual_repetitions,
        actual_duration_seconds=actual_duration_seconds,
        actual_distance_meters=actual_distance_meters,
        actual_weight_kg=actual_weight_kg,
        notes=notes,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def _generate_performance(db: Session, execution: WorkoutExecution) -> None:
    results = db.query(WorkoutExerciseExecution).filter(
        WorkoutExerciseExecution.execution_id == execution.id,
        WorkoutExerciseExecution.status == "done",
    ).all()
    for r in results:
        we = db.query(WorkoutExercise).filter(
            WorkoutExercise.id == r.workout_exercise_id,
        ).first()
        if not we:
            continue
        value = 0.0
        if we.sets and we.repetitions:
            value = float(we.sets) * float(we.repetitions)
        elif we.duration_seconds:
            value = float(we.duration_seconds)
        elif we.distance_meters:
            value = float(we.distance_meters)
        db.add(PerformanceRecord(
            athlete_id=execution.athlete_id,
            execution_id=execution.id,
            metric="volume",
            value=value,
        ))
