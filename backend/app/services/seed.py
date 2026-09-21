from sqlalchemy.orm import Session
from app.models.models import Sport, Position, SportAttribute


def seed_sports(db: Session):
    existing = db.query(Sport).first()
    if existing:
        return

    volleyball = Sport(name="Volei", icon="\U0001f3d0")
    basketball = Sport(name="Basquete", icon="\U0001f3c0")
    db.add_all([volleyball, basketball])
    db.flush()

    volleyball_positions = [
        Position(name="Levantador", sport_id=volleyball.id),
        Position(name="Oposto", sport_id=volleyball.id),
        Position(name="Ponteiro", sport_id=volleyball.id),
        Position(name="Central", sport_id=volleyball.id),
        Position(name="Libero", sport_id=volleyball.id),
    ]

    basketball_positions = [
        Position(name="Armador", sport_id=basketball.id),
        Position(name="Ala-armador", sport_id=basketball.id),
        Position(name="Ala", sport_id=basketball.id),
        Position(name="Ala-pivo", sport_id=basketball.id),
        Position(name="Pivo", sport_id=basketball.id),
    ]

    db.add_all(volleyball_positions + basketball_positions)

    volleyball_attributes = [
        SportAttribute(name="Saque", sport_id=volleyball.id),
        SportAttribute(name="Recepcao", sport_id=volleyball.id),
        SportAttribute(name="Ataque", sport_id=volleyball.id),
        SportAttribute(name="Bloqueio", sport_id=volleyball.id),
        SportAttribute(name="Defesa", sport_id=volleyball.id),
        SportAttribute(name="Levantamento", sport_id=volleyball.id),
        SportAttribute(name="Velocidade", sport_id=volleyball.id),
        SportAttribute(name="Resistencia", sport_id=volleyball.id),
    ]

    basketball_attributes = [
        SportAttribute(name="Arremesso", sport_id=basketball.id),
        SportAttribute(name="Passe", sport_id=basketball.id),
        SportAttribute(name="Drible", sport_id=basketball.id),
        SportAttribute(name="Defesa", sport_id=basketball.id),
        SportAttribute(name="Rebote", sport_id=basketball.id),
        SportAttribute(name="Velocidade", sport_id=basketball.id),
        SportAttribute(name="Resistencia", sport_id=basketball.id),
        SportAttribute(name="Controle de bola", sport_id=basketball.id),
    ]

    db.add_all(volleyball_attributes + basketball_attributes)
    db.commit()
