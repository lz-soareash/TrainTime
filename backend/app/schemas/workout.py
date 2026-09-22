from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class WorkoutCreate(BaseModel):
    team_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    scheduled_at: datetime
    duration_minutes: Optional[int] = Field(None, gt=0)


class WorkoutUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern=r"^(scheduled|completed|cancelled)$")


class TeamBasic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    team: TeamBasic
    title: str
    description: str | None = None
    scheduled_at: datetime
    duration_minutes: int | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class WorkoutListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    team_name: str
    title: str
    scheduled_at: datetime
    duration_minutes: int | None = None
    status: str
