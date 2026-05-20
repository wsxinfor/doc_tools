import uuid
import logging

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import CreateUserRequest

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, username: str, password: str) -> User:
    """验证用户名密码，返回 User 对象。失败统一返回 401，不泄露具体原因。"""
    user: User | None = db.query(User).filter(User.username == username).first()
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("用户名或密码错误")
    if not user.is_active:
        raise ForbiddenError("账号已停用，请联系管理员")
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id), role=user.role)


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise NotFoundError("用户")
    return user


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at).all()  # type: ignore[return-value]


def create_user(db: Session, req: CreateUserRequest) -> User:
    existing: User | None = db.query(User).filter(User.username == req.username).first()
    if existing is not None:
        raise BusinessRuleError("USERNAME_TAKEN", "用户名已存在")
    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user %s (role=%s)", user.username, user.role)
    return user


def toggle_user_active(db: Session, user_id: uuid.UUID) -> User:
    user = get_user_by_id(db, user_id)
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    logger.info("Toggled user %s is_active -> %s", user.username, user.is_active)
    return user
