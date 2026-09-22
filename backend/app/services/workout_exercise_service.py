from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.models import WorkoutExercise, Workout, Team, Exercise, Coach


def get_workout_exercise_by_id(db: Session, we_id: int) -> WorkoutExercise | None:
    return db.query(WorkoutExercise).options(
        joinedload(WorkoutExercise.workout).joinedload(Workout.team),
        joinedload(WorkoutExercise.exercise).joinedload(Exercise.sport),
    ).filter(WorkoutExercise.id == we_id).first()


def _verify_workout_coach(db: Session, workout_id: int, coach_id: int) -> Workout:
    workout = db.query(Workout).options(
        joinedload(Workout.team),
    ).filter(Workout.id == workout_id).first()
    if not workout:
        raise LookupError("Treino nao encontrado")
    if workout.team.coach_id != coach_id:
        raise PermissionError("Acesso negado")
    return workout


def add_exercise_to_workout(db: Session, workout_id: int, coach_id: int,
                            exercise_id: int, order: int,
                            sets: int | None = None, repetitions: int | None = None,
                            duration_seconds: int | None = None,
                            distance_meters: float | None = None,
                            rest_seconds: int | None = None,
                            notes: str | None = None) -> WorkoutExercise:
    workout = _verify_workout_coach(db, workout_id, coach_id)

    exercise = db.query(Exercise).options(
        joinedload(Exercise.sport),
    ).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise LookupError("Exercicio nao encontrado")

    if exercise.sport_id != workout.team.sport_id:
        raise ValueError("Exercicio nao e compativel com o esporte da equipe")

    we = WorkoutExercise(
        workout_id=workout_id,
        exercise_id=exercise_id,
        order=order,
        sets=sets,
        repetitions=repetitions,
        duration_seconds=duration_seconds,
        distance_meters=distance_meters,
        rest_seconds=rest_seconds,
        notes=notes,
    )
    db.add(we)
    db.commit()
    db.refresh(we)
    return get_workout_exercise_by_id(db, we.id)


def list_workout_exercises(db: Session, workout_id: int, user_id: int, role: str) -> list[WorkoutExercise]:
    if role == "coach":
        coach = db.query(Coach).filter(Coach.user_id == user_id).first()
        if not coach:
            raise PermissionError("Acesso negado")
        workout = db.query(Workout).options(
            joinedload(Workout.team),
        ).filter(Workout.id == workout_id).first()
        if not workout:
            raise LookupError("Treino nao encontrado")
        if workout.team.coach_id != coach.id:
            raise PermissionError("Acesso negado")
    elif role == "athlete":
        from app.models.models import Athlete, TeamAthlete
        athlete = db.query(Athlete).filter(Athlete.user_id == user_id).first()
        if not athlete:
            raise PermissionError("Acesso negado")
        workout = db.query(Workout).filter(Workout.id == workout_id).first()
        if not workout:
            raise LookupError("Treino nao encontrado")
        is_member = db.query(TeamAthlete).filter(
            and_(TeamAthlete.team_id == workout.team_id, TeamAthlete.athlete_id == athlete.id)
        ).first()
        if not is_member:
            raise PermissionError("Acesso negado")
    else:
        raise PermissionError("Acesso negado")

    return db.query(WorkoutExercise).options(
        joinedload(WorkoutExercise.exercise).joinedload(Exercise.sport),
    ).filter(WorkoutExercise.workout_id == workout_id).order_by(WorkoutExercise.order.asc()).all()


def update_workout_exercise(db: Session, workout_id: int, we_id: int, coach_id: int,
                            order: int | None = None, sets: int | None = None,
                            repetitions: int | None = None,
                            duration_seconds: int | None = None,
                            distance_meters: float | None = None,
                            rest_seconds: int | None = None,
                            notes: str | None = None) -> WorkoutExercise:
    we = get_workout_exercise_by_id(db, we_id)
    if not we:
        raise LookupError("Exercicio do treino nao encontrado")
    if we.workout_id != workout_id:
        raise LookupError("Exercicio do treino nao encontrado")

    _verify_workout_coach(db, we.workout_id, coach_id)

    if order is not None:
        we.order = order
    if sets is not None:
        we.sets = sets
    if repetitions is not None:
        we.repetitions = repetitions
    if duration_seconds is not None:
        we.duration_seconds = duration_seconds
    if distance_meters is not None:
        we.distance_meters = distance_meters
    if rest_seconds is not None:
        we.rest_seconds = rest_seconds
    if notes is not None:
        we.notes = notes

    db.commit()
    return get_workout_exercise_by_id(db, we.id)


def delete_workout_exercise(db: Session, workout_id: int, we_id: int, coach_id: int) -> None:
    we = db.query(WorkoutExercise).filter(WorkoutExercise.id == we_id).first()
    if not we:
        raise LookupError("Exercicio do treino nao encontrado")
    if we.workout_id != workout_id:
        raise LookupError("Exercicio do treino nao encontrado")

    _verify_workout_coach(db, we.workout_id, coach_id)

    db.delete(we)
    db.commit()
