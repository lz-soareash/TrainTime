from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role, get_db
from app.models.models import User
from app.schemas.performance import (
    PerformanceCreate, PerformanceRecordResponse, PerformanceAggregateResponse,
)
from app.services import performance_service

router = APIRouter(prefix="/performance", tags=["performance"])


def format_record_response(r):
    return PerformanceRecordResponse(
        id=r.id,
        athlete_id=r.athlete_id,
        execution_id=r.execution_id,
        metric=r.metric,
        value=r.value,
        recorded_at=r.recorded_at,
        notes=r.notes,
    )


@router.post("", response_model=PerformanceRecordResponse,
             status_code=status.HTTP_201_CREATED)
def record_performance(
    data: PerformanceCreate,
    current_user: User = Depends(require_role("athlete")),
    db: Session = Depends(get_db),
):
    try:
        record = performance_service.record_performance(
            db, current_user.id, data.execution_id,
            data.metric, data.value, data.notes,
        )
        return format_record_response(record)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/records", response_model=list[PerformanceRecordResponse])
def list_my_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role == "athlete":
        try:
            records = performance_service.list_athlete_records(db, current_user.id)
            return [format_record_response(r) for r in records]
        except LookupError as e:
            raise HTTPException(status_code=404, detail=str(e))
    raise HTTPException(status_code=403, detail="Acesso negado")


@router.get("", response_model=list[PerformanceAggregateResponse])
def list_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        records = performance_service.list_performance(db, current_user.id, current_user.role)
        return records
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
