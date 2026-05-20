import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.auth import CreateUserRequest, UserListResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserListResponse:
    users = auth_service.list_users(db)
    return UserListResponse(data=[UserResponse.model_validate(u) for u in users])


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    req: CreateUserRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    user = auth_service.create_user(db, req)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/toggle", response_model=UserResponse)
def toggle_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    user = auth_service.toggle_user_active(db, user_id)
    return UserResponse.model_validate(user)
