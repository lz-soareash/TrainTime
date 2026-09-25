from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone

from app.models.models import (
    Goal, Athlete, Coach, Team, TeamAthlete, User,
)
from app.schemas.goal import GoalCreate, GoalUpdate


def _raise_not_found():
    raise LookupError("Meta nao encontrada")


def _raise_forbidden():
    raise PermissionError("Acesso negado")


def _progress_percentage(goal: Goal) -> int:
    if goal.target_value <= 0:
        return 0
    ratio = goal.current_value / goal.target_value
    return max(0, min(100, int(ratio * 100)))


def _get_athlete_or_raise(db: Session, user_id: int) -> Athlete:
    athlete = db.query(Athlete).filter(Athlete.user_id == user_id).first()
    if not athlete:
        raise LookupError("Perfil de atleta nao encontrado")
    return athlete


def _get_coach_or_raise(db: Session, user_id: int) -> Coach:
    coach = db.query(Coach).filter(Coach.user_id == user_id).first()
    if not coach:
        raise LookupError("Perfil de treinador nao encontrado")
    return coach


def _athlete_in_coach_teams(
    db: Session, coach_id: int, athlete_id: int,
) -> bool:
    rows = (
        db.query(TeamAthlete.athlete_id)
        .join(Team, Team.id == TeamAthlete.team_id)
        .filter(Team.coach_id == coach_id, TeamAthlete.athlete_id == athlete_id)
        .first()
    )
    return rows is not None


def _resolve_athlete_id(db: Session, role: str, user_id: int, data: GoalCreate) -> int:
    if role == "athlete":
        athlete = _get_athlete_or_raise(db, user_id)
        if data.athlete_id not in (None, athlete.id):
            _raise_forbidden()
        return athlete.id
    # coach: athlete_id obrigatorio e deve pertencer a uma team do coach
    coach = _get_coach_or_raise(db, user_id)
    if data.athlete_id is None:
        raise ValueError("athlete_id e obrigatorio para coach")
    if not _athlete_in_coach_teams(db, coach.id, data.athlete_id):
        _raise_forbidden()
    return data.athlete_id


def create_goal(
    db: Session, role: str, user_id: int, data: GoalCreate,
) -> Goal:
    athlete_id = _resolve_athlete_id(db, role, user_id, data)
    goal = Goal(
        athlete_id=athlete_id,
        created_by=user_id,
        title=data.title,
        description=data.description,
        metric=data.metric,
        target_value=data.target_value,
        current_value=data.current_value,
        unit=data.unit,
        deadline=data.deadline,
        status="completed" if data.current_value >= data.target_value else "active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def _authorized_goal_query(db: Session, role: str, user_id: int):
    if role == "athlete":
        athlete = _get_athlete_or_raise(db, user_id)
        return db.query(Goal).options(
            joinedload(Goal.athlete).joinedload(Athlete.user),
        ).filter(Goal.athlete_id == athlete.id)
    coach = _get_coach_or_raise(db, user_id)
    athlete_ids = (
        db.query(TeamAthlete.athlete_id)
        .join(Team, Team.id == TeamAthlete.team_id)
        .filter(Team.coach_id == coach.id)
        .distinct()
        .all()
    )
    ids = [row[0] for row in athlete_ids]
    if not ids:
        return db.query(Goal).filter(False)
    return db.query(Goal).options(
        joinedload(Goal.athlete).joinedload(Athlete.user),
    ).filter(Goal.athlete_id.in_(ids))


def list_goals(
    db: Session, role: str, user_id: int,
    athlete_id: int | None = None, status: str | None = None,
):
    query = _authorized_goal_query(db, role, user_id)
    if athlete_id is not None:
        query = query.filter(Goal.athlete_id == athlete_id)
    if status is not None:
        query = query.filter(Goal.status == status)
    return query.order_by(Goal.deadline.asc()).all()


def get_goal(db: Session, role: str, user_id: int, goal_id: int) -> Goal:
    query = _authorized_goal_query(db, role, user_id)
    goal = query.filter(Goal.id == goal_id).first()
    if not goal:
        _raise_not_found()
    return goal


def update_goal(
    db: Session, role: str, user_id: int, goal_id: int, data: GoalUpdate,
) -> Goal:
    goal = get_goal(db, role, user_id, goal_id)
    if role == "athlete":
        athlete = _get_athlete_or_raise(db, user_id)
        if goal.athlete_id != athlete.id:
            _raise_forbidden()
    else:
        if goal.created_by != user_id:
            _raise_forbidden()

    updates = data.model_dump(exclude_unset=True)
    if "athlete_id" in updates or "created_by" in updates or "id" in updates:
        raise ValueError("Campos imutaveis nao podem ser alterados")
    for field in ("title", "description", "metric", "target_value",
                  "current_value", "unit", "deadline", "status"):
        if field in updates:
            setattr(goal, field, updates[field])

    if goal.current_value >= goal.target_value:
        goal.status = "completed"
    goal.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(goal)
    return goal


def cancel_goal(db: Session, role: str, user_id: int, goal_id: int) -> Goal:
    goal = get_goal(db, role, user_id, goal_id)
    if role == "athlete":
        athlete = _get_athlete_or_raise(db, user_id)
        if goal.athlete_id != athlete.id:
            _raise_forbidden()
    else:
        if goal.created_by != user_id:
            _raise_forbidden()
    goal.status = "cancelled"
    goal.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(goal)
    return goal
