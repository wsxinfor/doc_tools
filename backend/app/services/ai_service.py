import logging

from sqlalchemy.orm import Session

from app.adapters.base import AIAdapter
from app.adapters.factory import get_ai_adapter
from app.core.encryption import decrypt_value, encrypt_value
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)

_KEY_PROVIDER = "ai_provider"
_KEY_API_KEY = "ai_api_key"
_KEY_MODEL_URL = "ai_model_url"
_KEY_MODEL_NAME = "ai_model_name"


# ──────────────────────────────────────────
# Config helpers
# ──────────────────────────────────────────

def _get_config(db: Session, key: str) -> str | None:
    row: SystemConfig | None = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else None


def _set_config(db: Session, key: str, value: str) -> None:
    row: SystemConfig | None = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row is None:
        row = SystemConfig(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    db.commit()


def get_ai_settings(db: Session) -> dict[str, object]:
    provider = _get_config(db, _KEY_PROVIDER) or "qwen"
    has_key = bool(_get_config(db, _KEY_API_KEY))
    model_url = _get_config(db, _KEY_MODEL_URL) or ""
    model_name = _get_config(db, _KEY_MODEL_NAME) or ""
    return {"provider": provider, "has_api_key": has_key, "model_url": model_url, "model_name": model_name}


def update_ai_settings(
    db: Session, provider: str, api_key: str, model_url: str = "", model_name: str = ""
) -> None:
    _set_config(db, _KEY_PROVIDER, provider)
    encrypted = encrypt_value(api_key)
    _set_config(db, _KEY_API_KEY, encrypted)
    _set_config(db, _KEY_MODEL_URL, model_url)
    _set_config(db, _KEY_MODEL_NAME, model_name)
    logger.info("AI settings updated: provider=%s", provider)


def _get_adapter(db: Session) -> AIAdapter:
    from app.core.config import settings  # noqa: PLC0415

    provider = _get_config(db, _KEY_PROVIDER) or settings.AI_PROVIDER
    encrypted_key = _get_config(db, _KEY_API_KEY)
    if encrypted_key:
        api_key = decrypt_value(encrypted_key)
    else:
        api_key = settings.QWEN_API_KEY if provider == "qwen" else settings.OPENAI_API_KEY
    model_url = _get_config(db, _KEY_MODEL_URL) or ""
    model_name = _get_config(db, _KEY_MODEL_NAME) or ""
    return get_ai_adapter(provider, api_key, model_url=model_url, model_name=model_name)


# ──────────────────────────────────────────
# AI operations
# ──────────────────────────────────────────

async def clean_document_text(db: Session, text: str) -> str:
    adapter = _get_adapter(db)
    return await adapter.clean_text(text)


async def extract_document_structure(db: Session, text: str) -> dict[str, object]:
    adapter = _get_adapter(db)
    return await adapter.extract_structure(text)


async def correct_structure(db: Session, sections: list[dict]) -> list[dict]:
    """AI 修正文档结构层级。"""
    adapter = _get_adapter(db)
    corrected = await adapter.correct_structure(sections)
    # 额外本地检查：确保标题层级逐级递增，不跳跃
    return _adjust_heading_levels(corrected)


def _adjust_heading_levels(sections: list[dict]) -> list[dict]:
    """确保标题层级逐级递增，不跳跃。

    规则：
    - 子标题的层级不能超过父标题层级 +1
    - 如果检测到跳跃（如 L1→L4），自动调整为 L2
    """
    result = []
    last_heading_level = 0  # 上一个标题的层级

    for s in sections:
        new_section = s.copy()
        if s.get("paragraph_type") == "heading":
            current_level = s.get("level", 1)
            # 如果当前标题层级比上一个标题层级 +1 还大，调整为 last_heading_level + 1
            if current_level > last_heading_level + 1:
                new_section["level"] = last_heading_level + 1
                current_level = last_heading_level + 1
            last_heading_level = current_level
        result.append(new_section)

    return result


async def identify_headings_from_sections(db: Session, sections: list[dict]) -> list[dict]:
    """AI 识别文档标题（基于语义理解和格式提示）。

    Args:
        db: 数据库会话
        sections: DocumentExtractor 提取的 sections 列表（包含 is_bold/is_heiti 特征）

    Returns:
        合并 AI 识别结果后的 sections 列表
    """
    from app.services.document_extractor import DocumentExtractor  # noqa: PLC0415

    adapter = _get_adapter(db)

    # 1. 将 sections 编码为带格式提示的文本
    format_text_lines = []
    for i, sec in enumerate(sections):
        text = sec.get("text", "")
        ptype = sec.get("paragraph_type", "body")

        if ptype == "heading":
            # 已识别的标题，用 [H1]/[H2] 等标记
            level = sec.get("level", 1)
            format_text_lines.append(f"[H{level}]{text}[/H{level}]")
        elif ptype == "body" and text:
            # 正文：根据加粗/黑体特征添加标记
            if sec.get("is_bold"):
                format_text_lines.append(f"[B]{text}[/B]")
            elif sec.get("is_heiti"):
                format_text_lines.append(f"[H]{text}[/H]")
            else:
                format_text_lines.append(text)
        else:
            # 表格/图片/空段落
            format_text_lines.append(f"[{ptype.upper()}]")

    format_text = '\n'.join(format_text_lines)

    # 2. 调用 AI 识别标题
    try:
        ai_result = await adapter.identify_headings(format_text)
        logger.info("AI identified %d headings from %d sections",
                    sum(1 for item in ai_result if item.get("is_heading")), len(sections))
    except Exception as exc:
        logger.error("AI identify_headings failed: %s", exc)
        # 失败时返回原始 sections，不阻断流程
        return sections

    # 3. 合并 AI 结果到 sections
    merged = DocumentExtractor.merge_ai_headings(sections, ai_result)
    logger.info("Merged AI headings: %d total sections", len(merged))

    # 4. 本地校验和调整标题层级
    return _adjust_heading_levels(merged)
