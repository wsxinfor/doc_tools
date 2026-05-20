import uuid
from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise UnauthorizedError()
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise UnauthorizedError()

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UnauthorizedError()
    if not user.is_active:
        raise ForbiddenError("账号已停用")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise ForbiddenError("需要管理员权限")
    return current_user
