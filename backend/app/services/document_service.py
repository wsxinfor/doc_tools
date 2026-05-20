import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models.document import Document
from app.models.user import User
from app.services.md_parser import detect_markdown

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"docx", "md", "txt"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _validate_upload(file: UploadFile, size: int) -> str:
    """校验文件类型和大小，返回文件扩展名。"""
    original = file.filename or ""
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessRuleError(
            "INVALID_FILE_TYPE",
            f"不支持的文件格式 .{ext}，仅允许 .docx / .md / .txt",
        )
    if size > MAX_BYTES:
        raise BusinessRuleError(
            "FILE_TOO_LARGE",
            f"文件超过 {settings.MAX_FILE_SIZE_MB}MB 上限",
        )
    return ext


async def upload_document(db: Session, file: UploadFile, uploader: User) -> Document:
    content = await file.read()
    size = len(content)
    ext = _validate_upload(file, size)

    # 存储路径：{UPLOAD_DIR}/{user_id}/{uuid}.{ext}
    user_dir = Path(settings.UPLOAD_DIR) / str(uploader.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid.uuid4()
    dest = user_dir / f"{file_id}.{ext}"
    dest.write_bytes(content)

    doc = Document(
        filename=file.filename or f"{file_id}.{ext}",
        file_path=str(dest),
        file_type=ext,
        source_type="file",
        file_size=size,
        uploader_id=uploader.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Uploaded document %s (%d bytes) by user %s", doc.filename, size, uploader.id)
    return doc


def create_document_from_text(
    db: Session,
    filename: str,
    file_type: str,
    source_type: str,
    content: str | None,
    file_size: int,
    user: User,
) -> Document:
    """从文本内容创建文档

    Args:
        db: 数据库会话
        filename: 文件名
        file_type: 文件类型 "md" | "txt"
        source_type: 来源类型 "text"
        content: 文本内容
        file_size: 文件大小（字符数）
        user: 当前用户

    Returns:
        Document: 创建的文档记录
    """
    # 自动检测是否为 Markdown
    if content and file_type == "txt":
        if detect_markdown(content):
            file_type = "md"

    doc = Document(
        filename=filename,
        file_path=None,  # 文本模式无文件路径
        file_type=file_type,
        source_type=source_type,
        content=content,
        file_size=file_size,
        uploader_id=user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    logger.info("Created text document %s (%d bytes) by user %s", filename, file_size, user.id)
    return doc


def list_documents(db: Session, current_user: User) -> list[Document]:
    q = db.query(Document).filter(Document.is_deleted.is_(False))
    if current_user.role != "admin":
        q = q.filter(Document.uploader_id == current_user.id)
    return q.order_by(Document.created_at.desc()).all()  # type: ignore[return-value]


def get_document(db: Session, doc_id: uuid.UUID, current_user: User) -> Document:
    doc: Document | None = (
        db.query(Document)
        .filter(Document.id == doc_id, Document.is_deleted.is_(False))
        .first()
    )
    if doc is None:
        raise NotFoundError("文档")
    if current_user.role != "admin" and doc.uploader_id != current_user.id:
        raise ForbiddenError("无权访问该文档")
    return doc


def delete_document(db: Session, doc_id: uuid.UUID, current_user: User) -> Document:
    doc = get_document(db, doc_id, current_user)

    # 级联删除关联的 RenderTask（文档本身软删除，render task 硬删除）
    _cascade_delete_render_tasks(db, doc_id)

    doc.is_deleted = True
    db.commit()
    db.refresh(doc)
    logger.info("Soft-deleted document %s by user %s", doc_id, current_user.id)
    return doc


def _cascade_delete_render_tasks(db: Session, doc_id: uuid.UUID) -> None:
    """删除文档关联的所有排版任务。"""
    try:
        from app.models.render_task import RenderTask  # noqa: PLC0415
        db.query(RenderTask).filter(RenderTask.document_id == doc_id).delete()
    except ImportError:
        pass
