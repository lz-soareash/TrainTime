from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.models import (
    PerformanceRecord, Athlete, User, PerformanceRecord, WorkoutExecution,
)
from app.schemas.performance import PerformanceAggregateResponse


def get_athlete_or_raise(db: Session, user_id: int) -> Athlete:
    athlete = db.query(Athlete).options(
        joinedload(Athlete.user),
    ).filter(Athlete.user_id == user_id).first()
    if not athlete:
        raise LookupError("Perfil de atleta nao encontrado")
    return athlete


def get_coach_id_or_raise(db: Session, user_id: int) -> int:
    from app.models.models import Coach
    coach = db.query(Coach).filter(Coach.user_id == user_id).first()
    if not coach:
        raise LookupError("Perfil de treinador nao encontrado")
    return coach.id


def record_performance(db: Session, athlete_user_id: int,
                       execution_id: int | None,
                       metric: str, value: float,
                       notes: str | None = None) -> PerformanceRecord:
    athlete = get_athlete_or_raise(db, athlete_user_id)
    if execution_id is not None:
        from app.models.models import WorkoutExecution
        execution = db.query(WorkoutExecution).filter(
            WorkoutExecution.id == execution_id,
        ).first()
        if not execution:
            raise LookupError("Execucao nao encontrada")
        if execution.athlete_id != athlete.id:
            raise PermissionError("Acesso negado")

    record = PerformanceRecord(
        athlete_id=athlete.id,
        execution_id=execution_id,
        metric=metric,
        value=value,
        recorded_at=datetime.now(timezone.utc),
        notes=notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_athlete_records(db: Session, athlete_user_id: int) -> list[PerformanceRecord]:
    athlete = get_athlete_or_raise(db, athlete_user_id)
    return db.query(PerformanceRecord).options(
        joinedload(PerformanceRecord.execution),
    ).filter(PerformanceRecord.athlete_id == athlete.id).order_by(
        PerformanceRecord.recorded_at.desc(),
    ).all()


def list_performance(db: Session, user_id: int, role: str,
                     athlete_id: int | None = None,
                     metric: str | None = None) -> list[PerformanceRecord]:
    query = db.query(PerformanceRecord).options(
        joinedload(PerformanceRecord.athlete).joinedload(Athlete.user),
        joinedload(PerformanceRecord.execution),
    )

    if role == "coach":
        coach_id = get_coach_id_or_raise(db, user_id)
        query = query.join(PerformanceRecord.execution).join(
            WorkoutExecution.workout,
        )
    elif role == "athlete":
        athlete = get_athlete_or_raise(db, user_id)
        query = query.filter(PerformanceRecord.athlete_id == athlete.id)
    else:
        raise PermissionError("Acesso negado")

    if athlete_id is not None:
        if role != "coach":
            raise PermissionError("Acesso negado")
        query = query.filter(PerformanceRecord.athlete_id == athlete_id)
    if metric is not None:
        query = query.filter(PerformanceRecord.metric == metric)

    records = query.order_by(PerformanceRecord.recorded_at.desc()).all()
    if role == "coach":
        return [
            PerformanceAggregateResponse(
                id=r.id,
                athlete_id=r.athlete_id,
                athlete_name=r.athlete.user.name if r.athlete and r.athlete.user else "Atleta",
                metric=r.metric,
                value=r.value,
                recorded_at=r.recorded_at,
                notes=r.notes,
            )
            for r in records
        ]
    return records
