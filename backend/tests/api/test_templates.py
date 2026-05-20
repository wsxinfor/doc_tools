"""M4 模板管理 API 测试。

验收标准：
- 模板 CRUD 全流程正常
- config 字段不符合 Schema 时 POST/PUT 返回 400/422 + 具体错误
- 被引用模板删除返回 422（M5 完成后生效）
- 列表全公司共享
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User


def _create_user(db: Session, username: str, role: str = "user") -> User:
    user = User(username=username, password_hash=hash_password("password123"), role=role)
    db.add(user)
    db.flush()
    return user


def _login(client: TestClient, username: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": "password123"})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _minimal_config() -> dict:
    return {}


def _create_template(client: TestClient, token: str, name: str = "My Template") -> dict:
    resp = client.post(
        "/api/templates",
        json={"name": name, "description": "desc", "config": _minimal_config()},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["data"]


# ──────────────────────────────────────────
# POST /api/templates
# ──────────────────────────────────────────

class TestCreate:
    def test_create_template_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_c1")
        token = _login(client, "tmpl_c1")
        resp = client.post(
            "/api/templates",
            json={"name": "Report Template", "description": "For reports", "config": {}},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "Report Template"
        assert "id" in data

    def test_create_template_empty_name_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_c2")
        token = _login(client, "tmpl_c2")
        resp = client.post(
            "/api/templates",
            json={"name": "", "config": {}},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_create_template_invalid_config_alignment_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_c3")
        token = _login(client, "tmpl_c3")
        # h1 alignment 值非法
        resp = client.post(
            "/api/templates",
            json={
                "name": "Bad Template",
                "config": {
                    "headings": {
                        "h1": {"font": {}, "spacing": {}, "alignment": "justify"},
                    }
                },
            },
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_create_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/templates", json={"name": "x", "config": {}})
        assert resp.status_code in (401, 403)


# ──────────────────────────────────────────
# GET /api/templates
# ──────────────────────────────────────────

class TestList:
    def test_list_shared_across_users(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_l1")
        _create_user(db, "tmpl_l2")
        t1 = _login(client, "tmpl_l1")
        t2 = _login(client, "tmpl_l2")

        _create_template(client, t1, "Template A")
        resp = client.get("/api/templates", headers=_auth(t2))
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()["data"]]
        assert "Template A" in names

    def test_list_excludes_deleted(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_l3")
        token = _login(client, "tmpl_l3")
        tmpl = _create_template(client, token, "ToDelete")
        tmpl_id = tmpl["id"]

        client.delete(f"/api/templates/{tmpl_id}", headers=_auth(token))

        resp = client.get("/api/templates", headers=_auth(token))
        ids = [t["id"] for t in resp.json()["data"]]
        assert tmpl_id not in ids


# ──────────────────────────────────────────
# GET /api/templates/:id
# ──────────────────────────────────────────

class TestDetail:
    def test_get_template_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_d1")
        token = _login(client, "tmpl_d1")
        tmpl = _create_template(client, token, "DetailTest")

        resp = client.get(f"/api/templates/{tmpl['id']}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "DetailTest"

    def test_get_nonexistent_returns_404(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_d2")
        token = _login(client, "tmpl_d2")
        resp = client.get("/api/templates/00000000-0000-0000-0000-000000000000", headers=_auth(token))
        assert resp.status_code == 404


# ──────────────────────────────────────────
# PUT /api/templates/:id
# ──────────────────────────────────────────

class TestUpdate:
    def test_creator_can_update(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_u1")
        token = _login(client, "tmpl_u1")
        tmpl = _create_template(client, token, "Original")

        resp = client.put(
            f"/api/templates/{tmpl['id']}",
            json={"name": "Updated"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated"

    def test_non_creator_cannot_update(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_u2")
        _create_user(db, "tmpl_u3")
        t_owner = _login(client, "tmpl_u2")
        t_other = _login(client, "tmpl_u3")
        tmpl = _create_template(client, t_owner, "OwnerTemplate")

        resp = client.put(
            f"/api/templates/{tmpl['id']}",
            json={"name": "Stolen"},
            headers=_auth(t_other),
        )
        assert resp.status_code == 403

    def test_admin_can_update_any(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_u4")
        _create_user(db, "tmpl_u4_admin", role="admin")
        t_user = _login(client, "tmpl_u4")
        t_admin = _login(client, "tmpl_u4_admin")
        tmpl = _create_template(client, t_user, "UserTemplate")

        resp = client.put(
            f"/api/templates/{tmpl['id']}",
            json={"name": "AdminUpdated"},
            headers=_auth(t_admin),
        )
        assert resp.status_code == 200

    def test_update_invalid_config_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_u5")
        token = _login(client, "tmpl_u5")
        tmpl = _create_template(client, token, "ConfigTest")

        resp = client.put(
            f"/api/templates/{tmpl['id']}",
            json={"config": {"body": {"font": {"size": "not-a-number"}}}},
            headers=_auth(token),
        )
        assert resp.status_code == 422


# ──────────────────────────────────────────
# DELETE /api/templates/:id
# ──────────────────────────────────────────

class TestDelete:
    def test_creator_can_delete(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_del1")
        token = _login(client, "tmpl_del1")
        tmpl = _create_template(client, token, "ToDelete")

        resp = client.delete(f"/api/templates/{tmpl['id']}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["is_deleted"] is True

    def test_non_creator_cannot_delete(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_del2")
        _create_user(db, "tmpl_del3")
        t_owner = _login(client, "tmpl_del2")
        t_other = _login(client, "tmpl_del3")
        tmpl = _create_template(client, t_owner, "Protected")

        resp = client.delete(f"/api/templates/{tmpl['id']}", headers=_auth(t_other))
        assert resp.status_code == 403

    def test_admin_can_delete_any(self, client: TestClient, db: Session) -> None:
        _create_user(db, "tmpl_del4")
        _create_user(db, "tmpl_del5_admin", role="admin")
        t_user = _login(client, "tmpl_del4")
        t_admin = _login(client, "tmpl_del5_admin")
        tmpl = _create_template(client, t_user, "UserOwned")

        resp = client.delete(f"/api/templates/{tmpl['id']}", headers=_auth(t_admin))
        assert resp.status_code == 200
