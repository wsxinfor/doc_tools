"""初始管理员账号创建脚本（仅首次执行一次）。

用法：
    cd backend
    python scripts/create_admin.py
"""
import sys
from pathlib import Path

# 将 backend/ 加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal  # noqa: E402
from app.core.exceptions import BusinessRuleError  # noqa: E402
from app.schemas.auth import CreateUserRequest  # noqa: E402
from app.services.auth_service import create_user  # noqa: E402


def main() -> None:
    username = input("管理员用户名 [admin]: ").strip() or "admin"
    password = input("管理员密码（最少 8 位）: ").strip()
    if len(password) < 8:
        print("密码不足 8 位，退出。")
        sys.exit(1)

    db = SessionLocal()
    try:
        req = CreateUserRequest(username=username, password=password, role="admin")
        user = create_user(db, req)
        print(f"管理员账号已创建：{user.username}（id={user.id}）")
    except BusinessRuleError as e:
        print(f"错误：{e.message}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
