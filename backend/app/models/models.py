from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "athlete" or "coach"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    athlete = relationship("Athlete", back_populates="user", uselist=False)
    coach = relationship("Coach", back_populates="user", uselist=False)


class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    icon = Column(String(10), nullable=True)

    positions = relationship("Position", back_populates="sport")
    attributes = relationship("SportAttribute", back_populates="sport")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)

    sport = relationship("Sport", back_populates="positions")


class SportAttribute(Base):
    __tablename__ = "sport_attributes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)

    sport = relationship("Sport", back_populates="attributes")


class Athlete(Base):
    __tablename__ = "athletes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)

    user = relationship("User", back_populates="athlete")
    sport = relationship("Sport")
    position = relationship("Position")
    teams = relationship("Team", secondary="team_athletes", back_populates="athletes")


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="coach")
    teams = relationship("Team", back_populates="coach")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)

    sport = relationship("Sport")
    coach = relationship("Coach", back_populates="teams")
    athletes = relationship("Athlete", secondary="team_athletes", back_populates="teams")


class TeamAthlete(Base):
    __tablename__ = "team_athletes"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
