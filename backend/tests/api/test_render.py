"""M5 排版引擎 API 测试。

验收标准：
- 创建排版任务立即返回 task_id，status=pending
- 异步执行，可轮询状态（通过 mock 直接设置为 done）
- 排版失败时 status=failed，error_message 有内容
- GET /render 返回历史列表
- 无权限用户访问他人任务返回 403
"""
import io
import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.document import Document
from app.models.render_task import RenderTask
from app.models.template import Template
from app.models.user import User

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


# ──────────────────────────────────────────
# helpers
# ──────────────────────────────────────────

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


def _upload_doc(client: TestClient, token: str) -> str:
    content = (FIXTURES_DIR / "sample.docx").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("sample.docx", io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _create_template(client: TestClient, token: str) -> str:
    resp = client.post(
        "/api/templates",
        json={"name": "Test Template", "config": {}},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


def _render_payload(doc_id: str, tmpl_id: str) -> dict:
    return {
        "document_id": doc_id,
        "template_id": tmpl_id,
        "ai_clean_result": "Cleaned text content.",
        "ai_structure": {
            "title": "Test Doc",
            "sections": [
                {"level": 1, "text": "Chapter 1", "paragraph_type": "heading", "children": []}
            ],
        },
        "render_params": {
            "client_name": "ACME Corp",
            "project_name": "Test Project",
            "doc_version": "1.0",
            "date": "2026-04-02",
        },
    }


# ──────────────────────────────────────────
# POST /api/render
# ──────────────────────────────────────────

class TestCreateRenderTask:
    def test_create_returns_task_id_pending(self, client: TestClient, db: Session) -> None:
        _create_user(db, "rnd_c1")
        token = _login(client, "rnd_c1")
        doc_id = _upload_doc(client, token)
        tmpl_id = _create_template(client, token)

        with patch("app.services.render_service.run_render_task"):
            resp = client.post(
                "/api/render",
                json=_render_payload(doc_id, tmpl_id),
                headers=_auth(token),
            )

        assert resp.status_code == 202
        body = resp.json()["data"]
        assert "id" in body
        assert body["status"] == "pending"

    def test_create_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/render", json={})
        assert resp.status_code in (401, 403)


# ──────────────────────────────────────────
# GET /api/render/:id/status
# ──────────────────────────────────────────

class TestGetStatus:
    def test_get_status_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "rnd_s1")
        token = _login(client, "rnd_s1")
        doc_id = _upload_doc(client, token)
        tmpl_id = _create_template(client, token)

        with patch("app.services.render_service.run_render_task"):
            create_resp = client.post(
                "/api/render",
                json=_render_payload(doc_id, tmpl_id),
                headers=_auth(token),
            )
        task_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/render/{task_id}/status", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == task_id

    def test_get_other_user_task_forbidden(self, client: TestClient, db: Session) -> None:
        _create_user(db, "rnd_s2")
        _create_user(db, "rnd_s3")
        t1 = _login(client, "rnd_s2")
        t2 = _login(client, "rnd_s3")
        doc_id = _upload_doc(client, t1)
        tmpl_id = _create_template(client, t1)

        with patch("app.services.render_service.run_render_task"):
            create_resp = client.post(
                "/api/render",
                json=_render_payload(doc_id, tmpl_id),
                headers=_auth(t1),
            )
        task_id = create_resp.json()["data"]["id"]

        resp = client.get(f"/api/render/{task_id}/status", headers=_auth(t2))
        assert resp.status_code == 403

    def test_get_nonexistent_task_returns_404(self, client: TestClient, db: Session) -> None:
        _create_user(db, "rnd_s4")
        token = _login(client, "rnd_s4")
        resp = client.get(
            "/api/render/00000000-0000-0000-0000-000000000000/status",
            headers=_auth(token),
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────
# GET /api/render (list)
# ──────────────────────────────────────────

class TestListRenderTasks:
    def test_list_returns_own_tasks(self, client: TestClient, db: Session) -> None:
        _create_user(db, "rnd_l1")
        _create_user(db, "rnd_l2")
        t1 = _login(client, "rnd_l1")
        t2 = _login(client, "rnd_l2")

        doc_id = _upload_doc(client, t1)
        tmpl_id = _create_template(client, t1)

        with patch("app.services.render_service.run_render_task"):
            client.post("/api/render", json=_render_payload(doc_id, tmpl_id), headers=_auth(t1))

        resp1 = client.get("/api/render", headers=_auth(t1))
        resp2 = client.get("/api/render", headers=_auth(t2))
        assert resp1.status_code == 200
        assert len(resp1.json()["data"]) >= 1
        assert len(resp2.json()["data"]) == 0


# ──────────────────────────────────────────
# Render engine integration (mock run_render_task)
# ──────────────────────────────────────────

class TestRenderEngine:
    def test_failed_task_records_error(self, client: TestClient, db: Session) -> None:
        """直接在数据库中模拟 failed 状态，验证 error_message 字段有值。"""
        _create_user(db, "rnd_e1")
        token = _login(client, "rnd_e1")
        doc_id = _upload_doc(client, token)
        tmpl_id = _create_template(client, token)

        with patch("app.services.render_service.run_render_task"):
            create_resp = client.post(
                "/api/render",
                json=_render_payload(doc_id, tmpl_id),
                headers=_auth(token),
            )
        task_id = create_resp.json()["data"]["id"]

        # 直接更新数据库模拟失败
        task = db.query(RenderTask).filter(RenderTask.id == uuid.UUID(task_id)).first()
        assert task is not None
        task.status = "failed"
        task.error_message = "Simulated render failure"
        db.commit()

        resp = client.get(f"/api/render/{task_id}/status", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "failed"
        assert data["error_message"] == "Simulated render failure"
