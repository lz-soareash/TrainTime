from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    sport_id: int


class TeamUpdate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class CoachBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SportBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None = None


class AthleteBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sport_id: int | None = None
    position_id: int | None = None
    position_name: str | None = None


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sport: SportBasic
    coach: CoachBasic
    athletes: list[AthleteBasic] = []
    created_at: datetime | None = None


class TeamListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sport: SportBasic
    athlete_count: int
    created_at: datetime | None = None
