from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_current_user
from app.database.connection import get_db
from app.models.models import User
from app.schemas.goal import (
    GoalCreate, GoalUpdate, GoalResponse,
)
from app.services import goal_service

router = APIRouter(tags=["goals"])


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        goal = goal_service.create_goal(
            db, current_user.role, current_user.id, data,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)
    return goal


@router.get("/goals", response_model=list[GoalResponse])
def list_goals(
    status_filter: Optional[str] = Query(None, alias="status"),
    athlete_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        goals = goal_service.list_goals(
            db, current_user.role, current_user.id,
            athlete_id=athlete_id, status=status_filter,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)
    return goals


@router.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        goal = goal_service.get_goal(
            db, current_user.role, current_user.id, goal_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)
    return goal


@router.put("/goals/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        goal = goal_service.update_goal(
            db, current_user.role, current_user.id, goal_id, data,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)
    return goal


@router.delete("/goals/{goal_id}", response_model=GoalResponse)
def cancel_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        goal = goal_service.cancel_goal(
            db, current_user.role, current_user.id, goal_id,
        )
    except Exception as exc:  # noqa: BLE001
        raise _http_error(exc)
    return goal
