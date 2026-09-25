from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class WorkoutExecutionCreate(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class ExerciseResultUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(pending|done|skipped)$")
    actual_sets: Optional[int] = Field(None, ge=0)
    actual_repetitions: Optional[int] = Field(None, ge=0)
    actual_duration_seconds: Optional[int] = Field(None, ge=0)
    actual_distance_meters: Optional[float] = Field(None, ge=0)
    actual_weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class WorkoutExecutionUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(in_progress|completed|cancelled)$")
    notes: Optional[str] = Field(None, max_length=500)
    finished_at: Optional[datetime] = None


class ExerciseBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    exercise_type: str


class ExerciseResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_exercise_id: int
    status: str
    actual_sets: int | None = None
    actual_repetitions: int | None = None
    actual_duration_seconds: int | None = None
    actual_distance_meters: float | None = None
    actual_weight_kg: float | None = None
    notes: str | None = None
    completed_at: datetime | None = None


class WorkoutExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    athlete_id: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkoutExecutionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_id: int
    athlete_id: int
    started_at: datetime
    finished_at: datetime | None = None
    status: str
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    exercise_results: list[ExerciseResultResponse] = []
