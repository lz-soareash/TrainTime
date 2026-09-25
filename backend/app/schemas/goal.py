from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import datetime
from typing import Optional


class GoalBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    athlete_id: Optional[int] = None
    created_by: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    metric: str = Field(..., min_length=1, max_length=100)
    target_value: float = Field(..., gt=0)
    current_value: float = Field(0, ge=0)
    unit: str = Field(..., min_length=1, max_length=50)
    deadline: datetime
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    metric: Optional[str] = Field(None, min_length=1, max_length=100)
    target_value: Optional[float] = Field(None, gt=0)
    current_value: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class GoalResponse(GoalBase):
    id: int

    @computed_field
    @property
    def progress_percentage(self) -> int:
        if self.target_value <= 0:
            return 0
        ratio = self.current_value / self.target_value
        return max(0, min(100, int(ratio * 100)))

    @computed_field
    @property
    def athlete_name(self) -> Optional[str]:
        athlete = getattr(self, "athlete", None)
        user = getattr(athlete, "user", None) if athlete is not None else None
        return user.name if user is not None else None
