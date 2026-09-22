from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class ExerciseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    sport_id: int
    exercise_type: str = Field("repetitions", pattern=r"^(repetitions|duration|distance|mixed)$")


class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    exercise_type: Optional[str] = Field(None, pattern=r"^(repetitions|duration|distance|mixed)$")


class SportBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None = None


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    sport_id: int
    sport: SportBasic
    exercise_type: str
    created_by: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ExerciseListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sport_id: int
    exercise_type: str
    created_by: int
