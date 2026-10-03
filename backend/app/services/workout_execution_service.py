from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.models import (
    Workout, WorkoutExecution, WorkoutExercise, WorkoutExerciseExecution,
    Athlete, Team, TeamAthlete, PerformanceRecord,
)

# Metricas geradas automaticamente ao concluir uma execucao.
AUTO_METRICS = ("volume", "carga")


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
                         athlete_id: int,
                         workout_id: int | None = None) -> WorkoutExecution:
    execution = _get_full(db, execution_id)
    if not execution:
        raise LookupError("Execucao nao encontrada")
    # O workout_id da URL precisa ser o mesmo da execucao: sem isso a rota
    # aceitaria /workouts/{qualquer}/executions/{id}.
    if workout_id is not None and execution.workout_id != workout_id:
        raise LookupError("Execucao nao pertence a esse treino")
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
                     finished_at: datetime | None = None,
                     workout_id: int | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id, workout_id)
    if status is not None:
        if status not in ("in_progress", "completed", "cancelled"):
            raise ValueError(f"Status invalido: {status}")
        if execution.status in ("completed", "cancelled") and status == "in_progress":
            raise ValueError("Execucao finalizada nao pode voltar para in_progress")
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
                       notes: str | None = None,
                       workout_id: int | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id, workout_id)
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
                     notes: str | None = None,
                     workout_id: int | None = None) -> WorkoutExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id, workout_id)
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
                          athlete_id: int,
                          workout_id: int | None = None) -> WorkoutExecution:
    return _verify_athlete_owns(db, execution_id, athlete_id, workout_id)


def get_execution_coach(db: Session, execution_id: int,
                        coach_id: int,
                        workout_id: int | None = None) -> WorkoutExecution:
    execution = _get_full(db, execution_id)
    if not execution:
        raise LookupError("Execucao nao encontrada")
    if workout_id is not None and execution.workout_id != workout_id:
        raise LookupError("Execucao nao pertence a esse treino")
    team = execution.workout.team
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")
    return execution


def add_exercise_result(db: Session, execution_id: int, athlete_id: int,
                        workout_exercise_id: int,
                        status="done", actual_sets=None, actual_repetitions=None,
                        actual_duration_seconds=None, actual_distance_meters=None,
                        actual_weight_kg=None, notes=None,
                        workout_id: int | None = None) -> WorkoutExerciseExecution:
    execution = _verify_athlete_owns(db, execution_id, athlete_id, workout_id)

    we = db.query(WorkoutExercise).filter(
        WorkoutExercise.id == workout_exercise_id,
        WorkoutExercise.workout_id == execution.workout_id,
    ).first()
    if not we:
        raise LookupError("Exercicio do treino nao encontrado")

    result = db.query(WorkoutExerciseExecution).filter(
        WorkoutExerciseExecution.execution_id == execution_id,
        WorkoutExerciseExecution.workout_exercise_id == workout_exercise_id,
    ).first()

    if result is None:
        result = WorkoutExerciseExecution(
            execution_id=execution_id,
            workout_exercise_id=workout_exercise_id,
        )
        db.add(result)

    result.status = status
    result.actual_sets = actual_sets
    result.actual_repetitions = actual_repetitions
    result.actual_duration_seconds = actual_duration_seconds
    result.actual_distance_meters = actual_distance_meters
    result.actual_weight_kg = actual_weight_kg
    result.notes = notes
    result.completed_at = (
        datetime.now(timezone.utc) if status == "done" else None
    )

    db.commit()
    db.refresh(result)
    return result


def result_metrics(r: WorkoutExerciseExecution) -> dict:
    """Volume e carga REALIZADOS de um exercicio.

    Nunca usa os valores planejados (WorkoutExercise): se o atleta nao
    registrou, o resultado e zero. Sem isso o painel mostraria a meta do
    treino como se fosse o que foi feito.
    """
    zero = {"volume": 0.0, "carga": 0.0}
    if r.status != "done":
        return zero
    volume = 0.0
    carga = 0.0
    if r.actual_sets is not None and r.actual_repetitions is not None:
        volume = float(r.actual_sets) * float(r.actual_repetitions)
        if r.actual_weight_kg:
            carga = volume * float(r.actual_weight_kg)
    elif r.actual_duration_seconds:
        volume = float(r.actual_duration_seconds)
    elif r.actual_distance_meters:
        volume = float(r.actual_distance_meters)
    return {"volume": volume, "carga": carga}


def _duration_seconds(start: datetime, end: datetime) -> float | None:
    """Diferenca entre dois timestamps, indiferente a fuso horario.

    O SQLite devolve started_at sem timezone enquanto finished_at e gravado
    em UTC; misturar os dois levanta TypeError. Ambos os valores sao UTC,
    entao basta remover o offset antes de subtrair.
    """
    if start is None or end is None:
        return None
    if start.tzinfo is not None:
        start = start.replace(tzinfo=None)
    if end.tzinfo is not None:
        end = end.replace(tzinfo=None)
    return (end - start).total_seconds()


def execution_metrics(db: Session, execution: WorkoutExecution) -> dict:
    """Totais realizados de uma execucao (volume, carga, duracao, aderencia)."""
    results = db.query(WorkoutExerciseExecution).options(
        joinedload(WorkoutExerciseExecution.workout_exercise),
    ).filter(WorkoutExerciseExecution.execution_id == execution.id).all()

    volume = 0.0
    carga = 0.0
    feitos = pulados = 0
    for r in results:
        if r.status == "done":
            feitos += 1
            m = result_metrics(r)
            volume += m["volume"]
            carga += m["carga"]
        elif r.status == "skipped":
            pulados += 1

    planejados = db.query(WorkoutExercise).filter(
        WorkoutExercise.workout_id == execution.workout_id,
    ).count()

    duracao = _duration_seconds(execution.started_at, execution.finished_at)

    aderencia = (feitos / planejados * 100.0) if planejados else 0.0
    return {
        "volume": round(volume, 2),
        "carga": round(carga, 2),
        "duracao_s": round(duracao, 1) if duracao is not None else None,
        "exercicios_planejados": planejados,
        "exercicios_feitos": feitos,
        "exercicios_pulados": pulados,
        "aderencia_pct": round(aderencia, 1),
    }


def coach_owns_athlete(db: Session, coach_id: int, athlete_id: int) -> bool:
    return db.query(TeamAthlete).join(Team).filter(
        Team.coach_id == coach_id,
        TeamAthlete.athlete_id == athlete_id,
    ).first() is not None


def _execution_item(db: Session, execution: WorkoutExecution) -> dict:
    return {
        "id": execution.id,
        "status": execution.status,
        "started_at": execution.started_at,
        "finished_at": execution.finished_at,
        **execution_metrics(db, execution),
        "delta": None,
    }


def compare_executions(db: Session, athlete_id: int, workout_id: int,
                       limit: int = 5) -> dict:
    """Historico do treino com deltas e previsao para a proxima execucao."""
    limit = max(1, min(limit, 20))
    executions = db.query(WorkoutExecution).filter(
        WorkoutExecution.workout_id == workout_id,
        WorkoutExecution.athlete_id == athlete_id,
    ).order_by(WorkoutExecution.started_at.desc()).limit(limit).all()

    # items[0] = mais recente; o delta de cada um compara com o anterior (mais antigo)
    items = [_execution_item(db, e) for e in executions]
    for i in range(len(items) - 1):
        atual, anterior = items[i], items[i + 1]
        if atual["status"] != "completed" or anterior["status"] != "completed":
            continue
        atual["delta"] = {
            "volume": round(atual["volume"] - anterior["volume"], 2),
            "carga": round(atual["carga"] - anterior["carga"], 2),
            "duracao_s": (
                round(atual["duracao_s"] - anterior["duracao_s"], 1)
                if atual["duracao_s"] is not None and anterior["duracao_s"] is not None
                else None
            ),
        }

    concluidas = [i for i in items if i["status"] == "completed"]
    amostra = concluidas[:3]
    forecast = {"volume": 0.0, "carga": 0.0, "duracao_s": 0.0, "amostra": len(amostra)}
    if amostra:
        forecast["volume"] = round(sum(i["volume"] for i in amostra) / len(amostra), 2)
        forecast["carga"] = round(sum(i["carga"] for i in amostra) / len(amostra), 2)
        com_duracao = [i["duracao_s"] for i in amostra if i["duracao_s"] is not None]
        if com_duracao:
            forecast["duracao_s"] = round(
                sum(com_duracao) / len(com_duracao), 1)

    return {"workout_id": workout_id, "executions": items, "forecast": forecast}


def _generate_performance(db: Session, execution: WorkoutExecution) -> None:
    """Grava as metricas automaticas da execucao, sem duplicar.

    Reabastece os registros a cada conclusao para refletir os resultados
    corrigidos depois (upsert logico por execution_id + metric).
    """
    db.query(PerformanceRecord).filter(
        PerformanceRecord.execution_id == execution.id,
        PerformanceRecord.metric.in_(AUTO_METRICS),
    ).delete(synchronize_session=False)

    metrics = execution_metrics(db, execution)
    for metric in AUTO_METRICS:
        value = metrics[metric]
        if value <= 0:
            continue
        db.add(PerformanceRecord(
            athlete_id=execution.athlete_id,
            execution_id=execution.id,
            metric=metric,
            value=value,
        ))
