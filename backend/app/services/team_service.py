from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.models.models import Team, TeamAthlete, Athlete, Sport, Coach, CoachSport, Workout, WorkoutExercise


def get_team_by_id(db: Session, team_id: int) -> Team | None:
    return db.query(Team).options(
        joinedload(Team.sport),
        joinedload(Team.coach).joinedload(Coach.user),
        joinedload(Team.athletes).joinedload(Athlete.position),
    ).filter(Team.id == team_id).first()


def create_team(db: Session, coach_id: int, name: str, sport_id: int) -> Team:
    sport = db.query(Sport).filter(Sport.id == sport_id).first()
    if not sport:
        raise ValueError("Esporte invalido")

    owns_sport = db.query(CoachSport).filter(
        and_(CoachSport.coach_id == coach_id, CoachSport.sport_id == sport_id)
    ).first()
    if not owns_sport:
        raise ValueError("Esporte nao cadastrado para este treinador")

    team = Team(name=name, sport_id=sport_id, coach_id=coach_id)
    db.add(team)
    db.commit()
    db.refresh(team)
    return get_team_by_id(db, team.id)


def list_coach_teams(db: Session, coach_id: int) -> list[dict]:
    teams = db.query(Team).options(
        joinedload(Team.sport),
    ).filter(Team.coach_id == coach_id).all()

    result = []
    for team in teams:
        athlete_count = db.query(TeamAthlete).filter(TeamAthlete.team_id == team.id).count()
        result.append({
            "id": team.id,
            "name": team.name,
            "sport": team.sport,
            "athlete_count": athlete_count,
        })
    return result


def update_team(db: Session, team_id: int, coach_id: int, name: str) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise LookupError("Equipe nao encontrada")
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    team.name = name
    db.commit()
    return get_team_by_id(db, team.id)


def delete_team(db: Session, team_id: int, coach_id: int) -> None:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise LookupError("Equipe nao encontrada")
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    workout_ids = [
        w.id for w in db.query(Workout).filter(Workout.team_id == team_id).all()
    ]
    if workout_ids:
        db.query(WorkoutExercise).filter(
            WorkoutExercise.workout_id.in_(workout_ids)
        ).delete(synchronize_session=False)
        db.query(Workout).filter(
            Workout.id.in_(workout_ids)
        ).delete(synchronize_session=False)

    db.query(TeamAthlete).filter(TeamAthlete.team_id == team_id).delete(synchronize_session=False)
    db.delete(team)
    db.commit()


def add_athlete_to_team(db: Session, team_id: int, athlete_id: int, coach_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise LookupError("Equipe nao encontrada")
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    athlete = db.query(Athlete).filter(Athlete.id == athlete_id).first()
    if not athlete:
        raise LookupError("Atleta nao encontrado")

    if athlete.sport_id != team.sport_id:
        raise ValueError("Atleta nao e compativel com o esporte da equipe")

    existing = db.query(TeamAthlete).filter(
        and_(TeamAthlete.team_id == team_id, TeamAthlete.athlete_id == athlete_id)
    ).first()
    if existing:
        raise ValueError("Atleta ja esta na equipe")

    link = TeamAthlete(team_id=team_id, athlete_id=athlete_id)
    db.add(link)
    db.commit()
    return get_team_by_id(db, team.id)


def remove_athlete_from_team(db: Session, team_id: int, athlete_id: int, coach_id: int) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise LookupError("Equipe nao encontrada")
    if team.coach_id != coach_id:
        raise PermissionError("Acesso negado")

    link = db.query(TeamAthlete).filter(
        and_(TeamAthlete.team_id == team_id, TeamAthlete.athlete_id == athlete_id)
    ).first()
    if not link:
        raise LookupError("Atleta nao esta na equipe")

    db.delete(link)
    db.commit()
    return get_team_by_id(db, team.id)


def list_athlete_teams(db: Session, athlete_id: int) -> list[dict]:
    links = db.query(TeamAthlete).filter(TeamAthlete.athlete_id == athlete_id).all()
    team_ids = [link.team_id for link in links]
    teams = db.query(Team).options(
        joinedload(Team.sport),
        joinedload(Team.coach).joinedload(Coach.user),
    ).filter(Team.id.in_(team_ids)).all()

    result = []
    for team in teams:
        result.append({
            "id": team.id,
            "name": team.name,
            "sport": team.sport,
            "coach_name": team.coach.user.name,
        })
    return result


def get_compatible_athletes(db: Session, sport_id: int, team_id: int) -> list[Athlete]:
    team_athlete_ids = db.query(TeamAthlete.athlete_id).filter(
        TeamAthlete.team_id == team_id
    ).subquery()

    athletes = db.query(Athlete).options(
        joinedload(Athlete.user),
        joinedload(Athlete.position),
    ).filter(
        and_(
            Athlete.sport_id == sport_id,
            ~Athlete.id.in_(team_athlete_ids),
        )
    ).all()

    return athletes
