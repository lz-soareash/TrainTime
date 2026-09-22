from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.models import Workout, Team, TeamAthlete, Athlete, Coach


def get_workout_by_id(db: Session, workout_id: int) -> Workout | None:
    return db.query(Workout).options(
        joinedload(Workout.team).joinedload(Team.coach),
        joinedload(Workout.team).joinedload(Team.sport),
    ).filter(Workout.id == workout_id).first()


def create_workout(db: Session, coach_id: int, team_id: int, title: str,
                   description: str | None, scheduled_at, duration_minutes: int | None) -> Workout:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise LookupError("Equipe nao encontrada")
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    workout = Workout(
        team_id=team_id,
        title=title,
        description=description,
        scheduled_at=scheduled_at,
        duration_minutes=duration_minutes,
        status="scheduled",
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return get_workout_by_id(db, workout.id)


def list_coach_workouts(db: Session, coach_id: int, team_id: int | None = None,
                        status: str | None = None) -> list[dict]:
    query = db.query(Workout).join(Team).options(
        joinedload(Workout.team),
    ).filter(Team.coach_id == coach_id)

    if team_id is not None:
        query = query.filter(Workout.team_id == team_id)
    if status is not None:
        query = query.filter(Workout.status == status)

    workouts = query.order_by(Workout.scheduled_at.asc()).all()

    result = []
    for w in workouts:
        result.append({
            "id": w.id,
            "team_id": w.team_id,
            "team_name": w.team.name,
            "title": w.title,
            "scheduled_at": w.scheduled_at,
            "duration_minutes": w.duration_minutes,
            "status": w.status,
        })
    return result


def list_athlete_workouts(db: Session, athlete_id: int, status: str | None = None) -> list[dict]:
    team_ids = [link.team_id for link in db.query(TeamAthlete).filter(TeamAthlete.athlete_id == athlete_id).all()]

    query = db.query(Workout).join(Team).options(
        joinedload(Workout.team),
    ).filter(Workout.team_id.in_(team_ids))

    if status is not None:
        query = query.filter(Workout.status == status)

    workouts = query.order_by(Workout.scheduled_at.asc()).all()

    result = []
    for w in workouts:
        result.append({
            "id": w.id,
            "team_id": w.team_id,
            "team_name": w.team.name,
            "title": w.title,
            "scheduled_at": w.scheduled_at,
            "duration_minutes": w.duration_minutes,
            "status": w.status,
        })
    return result


def get_workout_detail(db: Session, workout_id: int, user_id: int, role: str) -> Workout:
    workout = get_workout_by_id(db, workout_id)
    if not workout:
        raise LookupError("Treino nao encontrado")

    if role == "coach":
        coach = db.query(Coach).filter(Coach.user_id == user_id).first()
        if not coach or workout.team.coach_id != coach.id:
            raise PermissionError("Acesso negado")
    elif role == "athlete":
        athlete = db.query(Athlete).filter(Athlete.user_id == user_id).first()
        if not athlete:
            raise PermissionError("Acesso negado")
        is_member = db.query(TeamAthlete).filter(
            and_(TeamAthlete.team_id == workout.team_id, TeamAthlete.athlete_id == athlete.id)
        ).first()
        if not is_member:
            raise PermissionError("Acesso negado")

    return workout


def update_workout(db: Session, workout_id: int, coach_id: int,
                   title: str | None = None, description: str | None = None,
                   scheduled_at=None, duration_minutes: int | None = None,
                   status: str | None = None) -> Workout:
    workout = get_workout_by_id(db, workout_id)
    if not workout:
        raise LookupError("Treino nao encontrado")
    if workout.team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    if title is not None:
        workout.title = title
    if description is not None:
        workout.description = description
    if scheduled_at is not None:
        workout.scheduled_at = scheduled_at
    if duration_minutes is not None:
        workout.duration_minutes = duration_minutes
    if status is not None:
        workout.status = status

    db.commit()
    return get_workout_by_id(db, workout.id)


def delete_workout(db: Session, workout_id: int, coach_id: int) -> None:
    workout = db.query(Workout).filter(Workout.id == workout_id).first()
    if not workout:
        raise LookupError("Treino nao encontrado")
    if workout.team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    db.delete(workout)
    db.commit()
