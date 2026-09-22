from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class WorkoutExerciseCreate(BaseModel):
    exercise_id: int
    order: int = Field(..., gt=0)
    sets: Optional[int] = Field(None, gt=0)
    repetitions: Optional[int] = Field(None, gt=0)
    duration_seconds: Optional[int] = Field(None, gt=0)
    distance_meters: Optional[float] = Field(None, gt=0)
    rest_seconds: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class WorkoutExerciseUpdate(BaseModel):
    order: Optional[int] = Field(None, gt=0)
    sets: Optional[int] = Field(None, gt=0)
    repetitions: Optional[int] = Field(None, gt=0)
    duration_seconds: Optional[int] = Field(None, gt=0)
    distance_meters: Optional[float] = Field(None, gt=0)
    rest_seconds: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class ExerciseBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    exercise_type: str


class WorkoutExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    exercise_id: int
    exercise: ExerciseBasic
    order: int
    sets: int | None = None
    repetitions: int | None = None
    duration_seconds: int | None = None
    distance_meters: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
