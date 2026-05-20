"""M3 AI 处理 API 测试。

所有 AI Adapter 调用通过 mock 替换，避免真实 API 调用。

验收标准：
- 清洗接口返回清洗后文本
- 结构识别接口返回合法标题树 JSON
- AI 调用失败时返回降级响应（status=ai_failed）
- 速率限制生效（超限返回 429）
- API Key 不出现在任何响应中
- 管理员可切换 AI Provider（GET/PUT /api/admin/settings/ai）
"""
import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

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


def _login(client: TestClient, username: str) -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": "password123"})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload_doc(client: TestClient, token: str) -> str:
    """上传 sample.docx，返回 doc_id。"""
    content = (FIXTURES_DIR / "sample.docx").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("sample.docx", io.BytesIO(content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


_MOCK_STRUCTURE = {
    "title": "测试文档",
    "sections": [
        {"level": 1, "text": "第一章 概述", "paragraph_type": "heading", "children": []}
    ],
}


# ──────────────────────────────────────────
# POST /api/ai/clean
# ──────────────────────────────────────────

class TestClean:
    def test_clean_returns_cleaned_text(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_clean1")
        token = _login(client, "ai_clean1")
        doc_id = _upload_doc(client, token)

        with patch(
            "app.services.ai_service.clean_document_text",
            new=AsyncMock(return_value="已清洗的文本内容"),
        ):
            resp = client.post(
                "/api/ai/clean",
                json={"doc_id": doc_id},
                headers=_auth(token),
            )

        assert resp.status_code == 200
        assert resp.json()["cleaned_text"] == "已清洗的文本内容"

    def test_clean_ai_failure_returns_degraded(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_clean2")
        token = _login(client, "ai_clean2")
        doc_id = _upload_doc(client, token)

        with patch(
            "app.services.ai_service.clean_document_text",
            new=AsyncMock(side_effect=RuntimeError("API timeout")),
        ):
            resp = client.post(
                "/api/ai/clean",
                json={"doc_id": doc_id},
                headers=_auth(token),
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ai_failed"
        assert "手动" in body["message"]

    def test_clean_nonexistent_doc_returns_404(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_clean3")
        token = _login(client, "ai_clean3")
        resp = client.post(
            "/api/ai/clean",
            json={"doc_id": "00000000-0000-0000-0000-000000000000"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_clean_requires_auth(self, client: TestClient) -> None:
        resp = client.post("/api/ai/clean", json={"doc_id": "00000000-0000-0000-0000-000000000000"})
        assert resp.status_code in (401, 403)


# ──────────────────────────────────────────
# POST /api/ai/extract-structure
# ──────────────────────────────────────────

class TestExtractStructure:
    def test_extract_returns_valid_structure(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_struct1")
        token = _login(client, "ai_struct1")
        doc_id = _upload_doc(client, token)

        with patch(
            "app.services.ai_service.extract_document_structure",
            new=AsyncMock(return_value=_MOCK_STRUCTURE),
        ):
            resp = client.post(
                "/api/ai/extract-structure",
                json={"doc_id": doc_id, "cleaned_text": "第一章 概述\n本文档用于测试。"},
                headers=_auth(token),
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["structure"]["title"] == "测试文档"
        assert len(body["structure"]["sections"]) == 1

    def test_extract_ai_failure_returns_degraded(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_struct2")
        token = _login(client, "ai_struct2")
        doc_id = _upload_doc(client, token)

        with patch(
            "app.services.ai_service.extract_document_structure",
            new=AsyncMock(side_effect=ValueError("invalid json")),
        ):
            resp = client.post(
                "/api/ai/extract-structure",
                json={"doc_id": doc_id, "cleaned_text": "some text"},
                headers=_auth(token),
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ai_failed"

    def test_extract_empty_text_rejected(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_struct3")
        token = _login(client, "ai_struct3")
        doc_id = _upload_doc(client, token)

        resp = client.post(
            "/api/ai/extract-structure",
            json={"doc_id": doc_id, "cleaned_text": ""},
            headers=_auth(token),
        )
        assert resp.status_code == 422  # Pydantic min_length 校验


# ──────────────────────────────────────────
# GET/PUT /api/admin/settings/ai
# ──────────────────────────────────────────

class TestAdminAISettings:
    def test_admin_get_ai_settings(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_adm1", role="admin")
        token = _login(client, "ai_adm1")

        resp = client.get("/api/admin/settings/ai", headers=_auth(token))
        assert resp.status_code == 200
        body = resp.json()
        assert "provider" in body
        assert "has_api_key" in body

    def test_admin_update_ai_settings(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_adm2", role="admin")
        token = _login(client, "ai_adm2")

        resp = client.put(
            "/api/admin/settings/ai",
            json={"provider": "openai", "api_key": "sk-test-key"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["provider"] == "openai"
        assert resp.json()["has_api_key"] is True

    def test_api_key_not_in_response(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_adm3", role="admin")
        token = _login(client, "ai_adm3")

        client.put(
            "/api/admin/settings/ai",
            json={"provider": "qwen", "api_key": "secret-api-key"},
            headers=_auth(token),
        )
        resp = client.get("/api/admin/settings/ai", headers=_auth(token))
        resp_str = json.dumps(resp.json())
        assert "secret-api-key" not in resp_str

    def test_non_admin_cannot_update_settings(self, client: TestClient, db: Session) -> None:
        _create_user(db, "ai_nonadm")
        token = _login(client, "ai_nonadm")
        resp = client.put(
            "/api/admin/settings/ai",
            json={"provider": "qwen", "api_key": "key"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
