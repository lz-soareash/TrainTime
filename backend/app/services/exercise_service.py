from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.models import Exercise, Sport, WorkoutExercise, CoachSport


def get_exercise_by_id(db: Session, exercise_id: int) -> Exercise | None:
    return db.query(Exercise).options(
        joinedload(Exercise.sport),
    ).filter(Exercise.id == exercise_id).first()


def create_exercise(db: Session, coach_id: int, name: str, description: str | None,
                    sport_id: int, exercise_type: str) -> Exercise:
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise ValueError("Esporte invalido")

    owns_sport = db.query(CoachSport).filter(
        and_(CoachSport.coach_id == coach_id, CoachSport.sport_id == sport_id)
    ).first()
    if not owns_sport:
        raise ValueError("Esporte nao cadastrado para este treinador")

    exercise = Exercise(
        name=name,
        description=description,
        sport_id=sport_id,
        exercise_type=exercise_type,
        created_by=coach_id,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return get_exercise_by_id(db, exercise.id)


def list_exercises(db: Session, sport_id: int | None = None,
                   exercise_type: str | None = None) -> list[Exercise]:
    query = db.query(Exercise).options(joinedload(Exercise.sport))

    if sport_id is not None:
        query = query.filter(Exercise.sport_id == sport_id)
    if exercise_type is not None:
        query = query.filter(Exercise.exercise_type == exercise_type)

    return query.order_by(Exercise.name.asc()).all()


def update_exercise(db: Session, exercise_id: int, coach_id: int,
                    name: str | None = None, description: str | None = None,
                    exercise_type: str | None = None) -> Exercise:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise LookupError("Exercicio nao encontrado")
    if exercise.created_by != coach_id:
        raise PermissionError("Acesso negado")

    if name is not None:
        exercise.name = name
    if description is not None:
        exercise.description = description
    if exercise_type is not None:
        exercise.exercise_type = exercise_type

    db.commit()
    return get_exercise_by_id(db, exercise.id)


def delete_exercise(db: Session, exercise_id: int, coach_id: int) -> None:
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise LookupError("Exercicio nao encontrado")
    if exercise.created_by != coach_id:
        raise PermissionError("Acesso negado")

    usage = db.query(WorkoutExercise).filter(WorkoutExercise.exercise_id == exercise_id).first()
    if usage:
        raise ValueError("Exercicio esta sendo utilizado em treinos")

    db.delete(exercise)
    db.commit()
