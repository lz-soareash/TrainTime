from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None = None


class AthleteProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    sport_id: int | None = None
    position_id: int | None = None


class AthleteProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    email: str
    role: str
    sport: SportResponse | None = None
    position: PositionResponse | None = None
    created_at: datetime


class CoachProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    sport_ids: list[int] | None = None


class CoachProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    email: str
    role: str
    sports: list[SportResponse] = []
    created_at: datetime


class AthleteAttributeValue(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attribute_id: int
    attribute_name: str
    value: float


class AthleteAttributesUpdate(BaseModel):
    attributes: list[dict] = Field(..., min_length=1)
