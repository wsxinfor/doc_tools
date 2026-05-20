"""M6 预览与导出 API 测试。

验收标准：
- 预览接口返回 HTML 字符串（status=done 时）
- 下载接口返回 .docx 文件（status=done 时）
- 未完成任务请求预览/下载返回 422
- 无权限用户请求他人任务返回 403
"""
import io
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.render_task import RenderTask
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


def _create_done_task(client: TestClient, db: Session, token: str, tmp_path: Path) -> tuple[str, Path, Path]:
    """Create a render task and manually set it to done with fake output files."""
    doc_id = _upload_doc(client, token)
    tmpl_id = _create_template(client, token)

    with patch("app.services.render_service.run_render_task"):
        resp = client.post("/api/render", json=_render_payload(doc_id, tmpl_id), headers=_auth(token))
    assert resp.status_code == 202
    task_id = resp.json()["data"]["id"]

    # Create fake output files
    docx_file = tmp_path / f"{task_id}.docx"
    html_file = tmp_path / f"{task_id}_preview.html"
    docx_file.write_bytes(b"PK fake docx content")
    html_file.write_text("<html><body><h1>Preview</h1></body></html>", encoding="utf-8")

    # Set task to done with file paths
    task = db.query(RenderTask).filter(RenderTask.id == uuid.UUID(task_id)).first()
    assert task is not None
    task.status = "done"
    task.result_path = str(docx_file)
    task.preview_path = str(html_file)
    db.commit()

    return task_id, docx_file, html_file


# ──────────────────────────────────────────
# GET /api/render/:id/preview
# ──────────────────────────────────────────

class TestPreview:
    def test_preview_returns_html(self, client: TestClient, db: Session, tmp_path: Path) -> None:
        _create_user(db, "exp_p1")
        token = _login(client, "exp_p1")
        task_id, _, _ = _create_done_task(client, db, token, tmp_path)

        resp = client.get(f"/api/render/{task_id}/preview", headers=_auth(token))
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "<h1>Preview</h1>" in resp.text

    def test_preview_pending_task_returns_422(self, client: TestClient, db: Session) -> None:
        _create_user(db, "exp_p2")
        token = _login(client, "exp_p2")
        doc_id = _upload_doc(client, token)
        tmpl_id = _create_template(client, token)

        with patch("app.services.render_service.run_render_task"):
            resp = client.post("/api/render", json=_render_payload(doc_id, tmpl_id), headers=_auth(token))
        task_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/render/{task_id}/preview", headers=_auth(token))
        assert resp.status_code == 422

    def test_preview_other_user_task_returns_403(self, client: TestClient, db: Session, tmp_path: Path) -> None:
        _create_user(db, "exp_p3")
        _create_user(db, "exp_p4")
        t1 = _login(client, "exp_p3")
        t2 = _login(client, "exp_p4")
        task_id, _, _ = _create_done_task(client, db, t1, tmp_path)

        resp = client.get(f"/api/render/{task_id}/preview", headers=_auth(t2))
        assert resp.status_code == 403

    def test_preview_nonexistent_task_returns_404(self, client: TestClient, db: Session) -> None:
        _create_user(db, "exp_p5")
        token = _login(client, "exp_p5")
        resp = client.get(
            "/api/render/00000000-0000-0000-0000-000000000000/preview",
            headers=_auth(token),
        )
        assert resp.status_code == 404


# ──────────────────────────────────────────
# GET /api/render/:id/download
# ──────────────────────────────────────────

class TestDownload:
    def test_download_returns_docx(self, client: TestClient, db: Session, tmp_path: Path) -> None:
        _create_user(db, "exp_d1")
        token = _login(client, "exp_d1")
        task_id, docx_file, _ = _create_done_task(client, db, token, tmp_path)

        resp = client.get(f"/api/render/{task_id}/download", headers=_auth(token))
        assert resp.status_code == 200
        assert "wordprocessingml" in resp.headers["content-type"]
        assert resp.content == b"PK fake docx content"

    def test_download_pending_task_returns_422(self, client: TestClient, db: Session) -> None:
        _create_user(db, "exp_d2")
        token = _login(client, "exp_d2")
        doc_id = _upload_doc(client, token)
        tmpl_id = _create_template(client, token)

        with patch("app.services.render_service.run_render_task"):
            resp = client.post("/api/render", json=_render_payload(doc_id, tmpl_id), headers=_auth(token))
        task_id = resp.json()["data"]["id"]

        resp = client.get(f"/api/render/{task_id}/download", headers=_auth(token))
        assert resp.status_code == 422

    def test_download_other_user_task_returns_403(self, client: TestClient, db: Session, tmp_path: Path) -> None:
        _create_user(db, "exp_d3")
        _create_user(db, "exp_d4")
        t1 = _login(client, "exp_d3")
        t2 = _login(client, "exp_d4")
        task_id, _, _ = _create_done_task(client, db, t1, tmp_path)

        resp = client.get(f"/api/render/{task_id}/download", headers=_auth(t2))
        assert resp.status_code == 403

    def test_download_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/render/00000000-0000-0000-0000-000000000000/download")
        assert resp.status_code in (401, 403)
