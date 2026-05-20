"""M1 用户认证 API 测试。

验收标准：
- 正确账号密码返回 JWT Token
- 错误密码返回 401，提示"用户名或密码错误"（不泄露具体原因）
- 停用账号登录返回 403
- JWT 过期后接口返回 401（通过无效 token 模拟）
- 非 admin 调用 /api/admin/* 返回 403
- 密码使用 bcrypt hash 存储（验证 password_hash 不等于明文）
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


# ──────────────────────────────────────────
# helpers
# ──────────────────────────────────────────

def _create_user(db: Session, username: str, password: str, role: str = "user", is_active: bool = True) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def _login(client: TestClient, username: str, password: str) -> dict:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()


# ──────────────────────────────────────────
# POST /api/auth/login
# ──────────────────────────────────────────

class TestLogin:
    def test_login_success_returns_token(self, client: TestClient, db: Session) -> None:
        _create_user(db, "alice", "password123")
        resp = client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == "alice"

    def test_login_wrong_password_returns_401(self, client: TestClient, db: Session) -> None:
        _create_user(db, "bob", "correct_pass")
        resp = client.post("/api/auth/login", json={"username": "bob", "password": "wrong_pass"})
        assert resp.status_code == 401
        body = resp.json()
        assert "用户名或密码错误" in body["message"]
        # 不泄露 "密码错误" vs "用户不存在"
        assert "密码" not in body["message"] or "用户名" in body["message"]

    def test_login_nonexistent_user_returns_401(self, client: TestClient) -> None:
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "any_pass"})
        assert resp.status_code == 401

    def test_login_inactive_user_returns_403(self, client: TestClient, db: Session) -> None:
        _create_user(db, "carol", "password123", is_active=False)
        resp = client.post("/api/auth/login", json={"username": "carol", "password": "password123"})
        assert resp.status_code == 403

    def test_password_stored_as_bcrypt_hash(self, db: Session) -> None:
        user = _create_user(db, "dave", "my_secret_pw")
        assert user.password_hash != "my_secret_pw"
        assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")


# ──────────────────────────────────────────
# GET /api/auth/me
# ──────────────────────────────────────────

class TestMe:
    def _get_token(self, client: TestClient, db: Session, username: str = "eve") -> str:
        _create_user(db, username, "password123")
        body = _login(client, username, "password123")
        return body["access_token"]

    def test_me_returns_current_user(self, client: TestClient, db: Session) -> None:
        token = self._get_token(client, db)
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "eve"

    def test_me_invalid_token_returns_401(self, client: TestClient) -> None:
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    def test_me_no_token_returns_403_or_401(self, client: TestClient) -> None:
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)


# ──────────────────────────────────────────
# POST /api/auth/logout
# ──────────────────────────────────────────

class TestLogout:
    def test_logout_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "frank", "password123")
        body = _login(client, "frank", "password123")
        token = body["access_token"]
        resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200


# ──────────────────────────────────────────
# GET /api/admin/users  (admin only)
# ──────────────────────────────────────────

class TestAdminUsers:
    def _admin_token(self, client: TestClient, db: Session) -> str:
        _create_user(db, "admin_user", "adminpass1", role="admin")
        body = _login(client, "admin_user", "adminpass1")
        return body["access_token"]

    def _user_token(self, client: TestClient, db: Session) -> str:
        _create_user(db, "normal_user", "userpass1", role="user")
        body = _login(client, "normal_user", "userpass1")
        return body["access_token"]

    def test_admin_can_list_users(self, client: TestClient, db: Session) -> None:
        token = self._admin_token(client, db)
        resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert "data" in resp.json()

    def test_non_admin_cannot_list_users(self, client: TestClient, db: Session) -> None:
        token = self._user_token(client, db)
        resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_can_create_user(self, client: TestClient, db: Session) -> None:
        token = self._admin_token(client, db)
        resp = client.post(
            "/api/admin/users",
            json={"username": "newbie", "password": "newpass99", "role": "user"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["username"] == "newbie"

    def test_create_user_duplicate_username_returns_422(self, client: TestClient, db: Session) -> None:
        token = self._admin_token(client, db)
        payload = {"username": "dup_user", "password": "password1", "role": "user"}
        client.post("/api/admin/users", json=payload, headers={"Authorization": f"Bearer {token}"})
        resp = client.post("/api/admin/users", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 422

    def test_create_user_short_password_returns_422(self, client: TestClient, db: Session) -> None:
        token = self._admin_token(client, db)
        resp = client.post(
            "/api/admin/users",
            json={"username": "shortpw", "password": "abc", "role": "user"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_admin_can_toggle_user(self, client: TestClient, db: Session) -> None:
        token = self._admin_token(client, db)
        # 创建一个用户
        create_resp = client.post(
            "/api/admin/users",
            json={"username": "toggleme", "password": "password1", "role": "user"},
            headers={"Authorization": f"Bearer {token}"},
        )
        user_id = create_resp.json()["id"]
        # 停用
        toggle_resp = client.put(
            f"/api/admin/users/{user_id}/toggle",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert toggle_resp.status_code == 200
        assert toggle_resp.json()["is_active"] is False
        # 再次启用
        toggle_resp2 = client.put(
            f"/api/admin/users/{user_id}/toggle",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert toggle_resp2.json()["is_active"] is True

    def test_non_admin_cannot_create_user(self, client: TestClient, db: Session) -> None:
        token = self._user_token(client, db)
        resp = client.post(
            "/api/admin/users",
            json={"username": "hacker", "password": "hacked123", "role": "admin"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
