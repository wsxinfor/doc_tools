import asyncio
import logging
from pathlib import Path
import uuid as uuid_lib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.structure_task import StructureTask
from app.models.document import Document
from app.services.ai_service import correct_structure

logger = logging.getLogger(__name__)

# 独立的数据库引擎，用于后台任务
_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
_SessionLocal = sessionmaker(bind=_engine)


def _get_db_session():
    """为后台任务创建独立的数据库会话。"""
    return _SessionLocal()


def _run_async(coro):
    """在后台线程中安全运行 async 函数。"""
    return asyncio.run(coro)


def run_structure_task(db, task_id: uuid_lib.UUID) -> None:
    """执行结构识别任务（后台执行）。

    注意：db 参数来自 FastAPI 的 background_tasks，在响应返回后可能已失效。
    所以我们创建独立的数据库会话来操作。
    """
    task_db = _get_db_session()
    try:
        task = task_db.query(StructureTask).filter(StructureTask.id == task_id).first()
        if task is None:
            logger.error("StructureTask %s not found", task_id)
            return

        task.status = "processing"
        task_db.commit()

        # 获取文档信息
        doc = task_db.query(Document).filter(Document.id == task.document_id).first()
        if doc is None:
            raise FileNotFoundError(f"Document {task.document_id} not found")

        # 1. 提取结构化数据
        from app.services.document_extractor import DocumentExtractor  # noqa: PLC0415
        from app.services.md_parser import MarkdownParser  # noqa: PLC0415

        if doc.source_type == "text" and doc.content:
            sections = DocumentExtractor.extract_from_text(doc.content, doc.file_type)
        elif doc.file_type == "md":
            md_content = Path(doc.file_path).read_text(encoding="utf-8")
            parser = MarkdownParser()
            sections = parser.parse(md_content)
        else:
            extractor = DocumentExtractor(doc.file_path)
            sections = extractor.extract_all()

        logger.info("Document extracted: %d sections (including images/tables)", len(sections))

        # 2. AI 修正层级（使用 asyncio.run 而不是手动管理事件循环）
        logger.info("Starting AI correct_structure...")
        corrected_sections = _run_async(correct_structure(task_db, sections))
        logger.info("AI correct_structure completed: %d sections", len(corrected_sections))

        # 3. 构建结构数据
        structure = {
            "title": Path(doc.filename).stem,
            "sections": corrected_sections
        }

        # 4. 保存结果
        task.ai_structure = structure
        task.status = "done"
        task_db.commit()

        logger.info("StructureTask %s completed successfully", task_id)

    except Exception as exc:
        logger.error("StructureTask %s failed: %s", task_id, exc, exc_info=True)
        try:
            task = task_db.query(StructureTask).filter(StructureTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(exc)
                task_db.commit()
        except Exception as inner_exc:
            logger.error("Failed to update task status for %s: %s", task_id, inner_exc, exc_info=True)
    finally:
        task_db.close()
