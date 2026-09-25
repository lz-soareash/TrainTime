from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    athlete = relationship("Athlete", back_populates="user", uselist=False)
    coach = relationship("Coach", back_populates="user", uselist=False)


class Sport(Base):
    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    icon = Column(String(10), nullable=True)

    positions = relationship("Position", back_populates="sport")
    attributes = relationship("SportAttribute", back_populates="sport")
    exercises = relationship("Exercise", back_populates="sport")


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
    attributes = relationship("AthleteAttribute", back_populates="athlete")
    executions = relationship("WorkoutExecution", back_populates="athlete")
    goals = relationship("Goal", back_populates="athlete")
    performance_records = relationship("PerformanceRecord", back_populates="athlete")


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    user = relationship("User", back_populates="coach")
    teams = relationship("Team", back_populates="coach")
    sports = relationship("CoachSport", back_populates="coach")


class CoachSport(Base):
    __tablename__ = "coach_sports"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)

    coach = relationship("Coach", back_populates="sports")
    sport = relationship("Sport")


class AthleteAttribute(Base):
    __tablename__ = "athlete_attributes"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    attribute_id = Column(Integer, ForeignKey("sport_attributes.id"), nullable=False)
    value = Column(Float, nullable=False, default=0)

    athlete = relationship("Athlete", back_populates="attributes")
    attribute = relationship("SportAttribute")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sport = relationship("Sport")
    coach = relationship("Coach", back_populates="teams")
    athletes = relationship("Athlete", secondary="team_athletes", back_populates="teams")
    workouts = relationship("Workout", back_populates="team")


class TeamAthlete(Base):
    __tablename__ = "team_athletes"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="scheduled")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="workouts")
    exercises = relationship("WorkoutExercise", back_populates="workout", order_by="WorkoutExercise.order")
    executions = relationship("WorkoutExecution", back_populates="workout")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    sport_id = Column(Integer, ForeignKey("sports.id"), nullable=False)
    exercise_type = Column(String(20), nullable=False, default="repetitions")
    created_by = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sport = relationship("Sport", back_populates="exercises")
    creator = relationship("Coach")
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise")


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    order = Column(Integer, nullable=False, default=1)
    sets = Column(Integer, nullable=True)
    repetitions = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    distance_meters = Column(Float, nullable=True)
    rest_seconds = Column(Integer, nullable=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    workout = relationship("Workout", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")
    execution_results = relationship("WorkoutExerciseExecution", back_populates="workout_exercise")


class WorkoutExecution(Base):
    __tablename__ = "workout_executions"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="in_progress")
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    workout = relationship("Workout", back_populates="executions")
    athlete = relationship("Athlete", back_populates="executions")
    exercise_results = relationship("WorkoutExerciseExecution", back_populates="execution")
    performance_records = relationship("PerformanceRecord", back_populates="execution")


class WorkoutExerciseExecution(Base):
    __tablename__ = "workout_exercise_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("workout_executions.id"), nullable=False)
    workout_exercise_id = Column(Integer, ForeignKey("workout_exercises.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    actual_sets = Column(Integer, nullable=True)
    actual_repetitions = Column(Integer, nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    actual_distance_meters = Column(Float, nullable=True)
    actual_weight_kg = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    execution = relationship("WorkoutExecution", back_populates="exercise_results")
    workout_exercise = relationship("WorkoutExercise", back_populates="execution_results")


class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    execution_id = Column(Integer, ForeignKey("workout_executions.id"), nullable=True)
    metric = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    athlete = relationship("Athlete", back_populates="performance_records")
    execution = relationship("WorkoutExecution", back_populates="performance_records")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    metric = Column(String(100), nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False, default=0)
    unit = Column(String(50), nullable=False)
    deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    athlete = relationship("Athlete", back_populates="goals")
    creator = relationship("User")
