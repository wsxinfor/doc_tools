"""AI 结构 JSON 解析逻辑单元测试。"""
import json

import pytest


# ──────────────────────────────────────────
# helpers
# ──────────────────────────────────────────

def _parse(raw: str) -> dict:
    """模拟 AI adapter 解析 JSON 的逻辑（与 QwenAdapter/OpenAIAdapter 一致）。"""
    return json.loads(raw)


# ──────────────────────────────────────────
# 合法结构
# ──────────────────────────────────────────

class TestValidStructure:
    def test_minimal_structure(self) -> None:
        raw = json.dumps({"title": "文档", "sections": []})
        result = _parse(raw)
        assert result["title"] == "文档"
        assert result["sections"] == []

    def test_nested_sections(self) -> None:
        raw = json.dumps({
            "title": "测试文档",
            "sections": [
                {
                    "level": 1,
                    "text": "第一章",
                    "paragraph_type": "heading",
                    "children": [
                        {"level": 2, "text": "1.1 背景", "paragraph_type": "heading", "children": []},
                    ],
                }
            ],
        })
        result = _parse(raw)
        assert len(result["sections"]) == 1
        assert result["sections"][0]["level"] == 1
        assert len(result["sections"][0]["children"]) == 1

    def test_multiple_top_level_sections(self) -> None:
        raw = json.dumps({
            "title": "报告",
            "sections": [
                {"level": 1, "text": "第一章", "paragraph_type": "heading", "children": []},
                {"level": 1, "text": "第二章", "paragraph_type": "heading", "children": []},
            ],
        })
        result = _parse(raw)
        assert len(result["sections"]) == 2


# ──────────────────────────────────────────
# 非法 JSON
# ──────────────────────────────────────────

class TestInvalidStructure:
    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse("不是 JSON 的文字")

    def test_truncated_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse('{"title": "test"')

    def test_empty_string_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse("")


# ──────────────────────────────────────────
# 加密工具单元测试
# ──────────────────────────────────────────

class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self) -> None:
        import os
        os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:5433/x")
        os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key-32chars-ok!")
        os.environ.setdefault("APP_ENV", "test")

        from app.core.encryption import decrypt_value, encrypt_value

        original = "my-secret-api-key-12345"
        cipher = encrypt_value(original)
        assert cipher != original
        assert decrypt_value(cipher) == original

    def test_cipher_does_not_contain_plaintext(self) -> None:
        import os
        os.environ.setdefault("DATABASE_URL", "postgresql://x:x@localhost:5433/x")
        os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key-32chars-ok!")
        os.environ.setdefault("APP_ENV", "test")

        from app.core.encryption import encrypt_value

        api_key = "super-secret-key"
        cipher = encrypt_value(api_key)
        assert api_key not in cipher
