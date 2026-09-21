from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.models import User, Athlete, Coach, Sport, Position, CoachSport
from app.schemas.auth import (
    UserRegister, AthleteRegister, CoachRegister,
    UserLogin, Token, UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado",
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.flush()

    if data.role == "athlete":
        athlete = Athlete(user_id=user.id)
        db.add(athlete)
    elif data.role == "coach":
        coach = Coach(user_id=user.id)
        db.add(coach)

    db.commit()
    db.refresh(user)
    return user


@router.post("/register/athlete", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_athlete(data: AthleteRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado",
        )

    sport = db.query(Sport).filter(Sport.id == data.sport_id).first()
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esporte invalido",
        )

    position = db.query(Position).filter(
        Position.id == data.position_id,
        Position.sport_id == data.sport_id,
    ).first()
    if not position:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Posicao invalida para o esporte selecionado",
        )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="athlete",
    )
    db.add(user)
    db.flush()

    athlete = Athlete(
        user_id=user.id,
        sport_id=data.sport_id,
        position_id=data.position_id,
    )
    db.add(athlete)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register/coach", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_coach(data: CoachRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ja cadastrado",
        )

    for sport_id in data.sport_ids:
        sport = db.query(Sport).filter(Sport.id == sport_id).first()
        if not sport:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Esporte ID {sport_id} invalido",
            )

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="coach",
    )
    db.add(user)
    db.flush()

    coach = Coach(user_id=user.id)
    db.add(coach)
    db.flush()

    for sport_id in data.sport_ids:
        coach_sport = CoachSport(coach_id=coach.id, sport_id=sport_id)
        db.add(coach_sport)

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
