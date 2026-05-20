"""M2 文档上传 API 测试。

验收标准：
- .docx 和 .md 上传成功，返回 doc_id 和元信息
- 非法格式（.pdf / .txt 等）被拒绝，返回 400 + 明确提示
- 超过 20MB 被拒绝
- 文档列表只返回当前用户的文档（admin 可见全部）
- 软删除后列表不再返回该文档
- 被引用的文档删除返回 422（M5 完成后再验证，此处跳过）
"""
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
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


def _login(client: TestClient, username: str, password: str = "password123") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload(client: TestClient, token: str, filename: str, content: bytes, content_type: str) -> object:
    return client.post(
        "/api/documents/upload",
        files={"file": (filename, io.BytesIO(content), content_type)},
        headers=_auth(token),
    )


# ──────────────────────────────────────────
# POST /api/documents/upload
# ──────────────────────────────────────────

class TestUpload:
    def test_upload_docx_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "u_docx")
        token = _login(client, "u_docx")
        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        resp = _upload(client, token, "sample.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["file_type"] == "docx"
        assert body["data"]["filename"] == "sample.docx"
        assert body["data"]["file_size"] == len(content)
        assert "id" in body["data"]

    def test_upload_md_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "u_md")
        token = _login(client, "u_md")
        content = (FIXTURES_DIR / "sample.md").read_bytes()
        resp = _upload(client, token, "sample.md", content, "text/markdown")
        assert resp.status_code == 201
        assert resp.json()["data"]["file_type"] == "md"

    def test_upload_pdf_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "u_pdf")
        token = _login(client, "u_pdf")
        resp = _upload(client, token, "report.pdf", b"%PDF-1.4 fake", "application/pdf")
        assert resp.status_code == 422
        body = resp.json()
        assert "pdf" in body["message"].lower() or "docx" in body["message"].lower()

    def test_upload_txt_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "u_txt")
        token = _login(client, "u_txt")
        resp = _upload(client, token, "notes.txt", b"hello", "text/plain")
        assert resp.status_code == 422

    def test_upload_oversized_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "u_big")
        token = _login(client, "u_big")
        # 21 MB
        big_content = b"\x00" * (21 * 1024 * 1024)
        resp = _upload(client, token, "huge.docx", big_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert resp.status_code == 422

    def test_upload_requires_auth(self, client: TestClient) -> None:
        content = b"fake"
        resp = client.post(
            "/api/documents/upload",
            files={"file": ("test.md", io.BytesIO(content), "text/markdown")},
        )
        assert resp.status_code in (401, 403)


# ──────────────────────────────────────────
# GET /api/documents
# ──────────────────────────────────────────

class TestList:
    def _upload_doc(self, client: TestClient, token: str, name: str = "sample.docx") -> str:
        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        resp = _upload(client, token, name, content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert resp.status_code == 201
        return resp.json()["data"]["id"]

    def test_list_returns_only_own_docs(self, client: TestClient, db: Session) -> None:
        _create_user(db, "list_u1")
        _create_user(db, "list_u2")
        t1 = _login(client, "list_u1")
        t2 = _login(client, "list_u2")
        self._upload_doc(client, t1, "u1doc.docx")
        self._upload_doc(client, t2, "u2doc.docx")

        resp = client.get("/api/documents", headers=_auth(t1))
        assert resp.status_code == 200
        docs = resp.json()["data"]
        assert len(docs) == 1
        assert docs[0]["filename"] == "u1doc.docx"

    def test_admin_sees_all_docs(self, client: TestClient, db: Session) -> None:
        _create_user(db, "list_regular")
        _create_user(db, "list_admin", role="admin")
        t_user = _login(client, "list_regular")
        t_admin = _login(client, "list_admin")
        self._upload_doc(client, t_user, "regdoc.docx")

        resp = client.get("/api/documents", headers=_auth(t_admin))
        assert resp.status_code == 200
        # admin sees at least the doc just uploaded
        doc_names = [d["filename"] for d in resp.json()["data"]]
        assert "regdoc.docx" in doc_names

    def test_list_excludes_deleted(self, client: TestClient, db: Session) -> None:
        _create_user(db, "list_del")
        token = _login(client, "list_del")
        doc_id = self._upload_doc(client, token, "todel.docx")

        # 软删除
        del_resp = client.delete(f"/api/documents/{doc_id}", headers=_auth(token))
        assert del_resp.status_code == 200

        # 列表不再出现
        resp = client.get("/api/documents", headers=_auth(token))
        ids = [d["id"] for d in resp.json()["data"]]
        assert doc_id not in ids


# ──────────────────────────────────────────
# GET /api/documents/:id
# ──────────────────────────────────────────

class TestDetail:
    def test_get_own_doc(self, client: TestClient, db: Session) -> None:
        _create_user(db, "det_u1")
        token = _login(client, "det_u1")
        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        up_resp = _upload(client, token, "sample.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_id = up_resp.json()["data"]["id"]

        resp = client.get(f"/api/documents/{doc_id}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == doc_id

    def test_get_other_user_doc_forbidden(self, client: TestClient, db: Session) -> None:
        _create_user(db, "det_owner")
        _create_user(db, "det_other")
        t_owner = _login(client, "det_owner")
        t_other = _login(client, "det_other")

        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        up_resp = _upload(client, t_owner, "secret.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_id = up_resp.json()["data"]["id"]

        resp = client.get(f"/api/documents/{doc_id}", headers=_auth(t_other))
        assert resp.status_code == 403

    def test_get_nonexistent_returns_404(self, client: TestClient, db: Session) -> None:
        _create_user(db, "det_404")
        token = _login(client, "det_404")
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = client.get(f"/api/documents/{fake_id}", headers=_auth(token))
        assert resp.status_code == 404


# ──────────────────────────────────────────
# DELETE /api/documents/:id
# ──────────────────────────────────────────

class TestDelete:
    def test_soft_delete_success(self, client: TestClient, db: Session) -> None:
        _create_user(db, "del_u1")
        token = _login(client, "del_u1")
        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        up_resp = _upload(client, token, "sample.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_id = up_resp.json()["data"]["id"]

        resp = client.delete(f"/api/documents/{doc_id}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["data"]["is_deleted"] is True

    def test_delete_other_user_doc_forbidden(self, client: TestClient, db: Session) -> None:
        _create_user(db, "del_owner")
        _create_user(db, "del_thief")
        t_owner = _login(client, "del_owner")
        t_thief = _login(client, "del_thief")

        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        up_resp = _upload(client, t_owner, "owner.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_id = up_resp.json()["data"]["id"]

        resp = client.delete(f"/api/documents/{doc_id}", headers=_auth(t_thief))
        assert resp.status_code == 403

    def test_admin_can_delete_any_doc(self, client: TestClient, db: Session) -> None:
        _create_user(db, "del_reg")
        _create_user(db, "del_admin_2", role="admin")
        t_user = _login(client, "del_reg")
        t_admin = _login(client, "del_admin_2")

        content = (FIXTURES_DIR / "sample.docx").read_bytes()
        up_resp = _upload(client, t_user, "owned.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        doc_id = up_resp.json()["data"]["id"]

        resp = client.delete(f"/api/documents/{doc_id}", headers=_auth(t_admin))
        assert resp.status_code == 200
