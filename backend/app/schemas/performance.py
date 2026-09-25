from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional


class PerformanceCreate(BaseModel):
    athlete_id: Optional[int] = None
    execution_id: Optional[int] = None
    metric: str = Field(..., min_length=1, max_length=50)
    value: float
    notes: Optional[str] = Field(None, max_length=500)


class PerformanceRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    execution_id: Optional[int] = None
    metric: str
    value: float
    recorded_at: datetime
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class PerformanceAggregateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    athlete_id: int
    athlete_name: str
    metric: str
    value: float
    recorded_at: datetime
    notes: Optional[str] = None


# Aliases mantidos para compatibilidade com documentacao de rotas
PerformanceRecordResponse = PerformanceRecord
PerformanceResponse = PerformanceRecord
