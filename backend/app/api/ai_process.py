import logging
import uuid as uuid_lib

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.structure_task import StructureTask
from app.schemas.ai import (
    AIFailedResponse,
    CleanRequest,
    CleanResponse,
    ExtractStructureRequest,
    ExtractStructureResponse,
)
from app.schemas.structure_task import (
    CreateStructureTaskRequest,
    StructureTaskDetailResponse,
    StructureTaskResponse,
    UpdateStructureRequest,
    UpdateStructureResponse,
    FindReplaceRequest,
)
from app.services import ai_service, document_service, structure_service

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _user_key(request: Request) -> str:
    """限流 key：按认证用户 ID 隔离（未认证时 fallback 到 IP）。"""
    user: User | None = getattr(request.state, "current_user", None)
    if user:
        return str(user.id)
    return get_remote_address(request)


@router.post("/clean", response_model=None)
@limiter.limit("10/minute", key_func=_user_key)
async def clean_document(
    request: Request,  # slowapi 需要 request 作为第一个参数
    req: CleanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CleanResponse | AIFailedResponse:
    doc = document_service.get_document(db, req.doc_id, current_user)
    content = ""
    try:
        content = _read_document_text(doc.file_path, doc.file_type)
        cleaned = await ai_service.clean_document_text(db, content)
        logger.info("AI clean succeeded for doc %s, text length=%d", req.doc_id, len(cleaned))
        return CleanResponse(cleaned_text=cleaned, original_text=content).model_dump()
    except Exception as exc:
        logger.error("AI clean failed for doc %s: %s", req.doc_id, exc, exc_info=True)
        return AIFailedResponse(original_text=content, message=str(exc)).model_dump()


@router.post("/extract-structure", response_model=None)
@limiter.limit("10/minute", key_func=_user_key)
async def extract_structure(
    request: Request,
    req: ExtractStructureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtractStructureResponse | AIFailedResponse:
    """从文档提取结构（同步模式，适用于小文档）。"""
    from pathlib import Path

    # 验证文档归属
    doc = document_service.get_document(db, req.doc_id, current_user)

    try:
        # 1. 使用 document_extractor 提取结构化数据
        from app.services.document_extractor import DocumentExtractor
        from app.services.md_parser import MarkdownParser  # noqa: PLC0415

        # 根据文档来源类型和文件格式选择提取方式
        if doc.source_type == "text" and doc.content:
            # 文本源：直接从 content 字段提取
            sections = DocumentExtractor.extract_from_text(doc.content, doc.file_type)
        elif doc.file_type == "md":
            # MD 文件：读取文件内容并用 MarkdownParser 解析
            from pathlib import Path  # noqa: PLC0415
            md_content = Path(doc.file_path).read_text(encoding="utf-8")
            parser = MarkdownParser()
            sections = parser.parse(md_content)
        else:
            # DOCX 文件：从文件路径提取
            extractor = DocumentExtractor(doc.file_path)
            sections = extractor.extract_all()

        logger.info("Document extracted: %d sections (including images/tables)", len(sections))

        # 2. 【新增】如果标题不足，触发 AI 语义识别
        if DocumentExtractor.has_insufficient_headings(sections):
            logger.info("Insufficient headings detected, triggering AI identification...")
            sections = await ai_service.identify_headings_from_sections(db, sections)

        # 3. AI 修正层级（只修正标题，表格/图片保持不变）
        corrected_sections = await ai_service.correct_structure(db, sections)

        # 4. 构建响应
        structure = {
            "title": Path(doc.filename).stem,  # 用文件名作为标题
            "sections": corrected_sections
        }

        logger.info("AI structure correction succeeded for doc %s", req.doc_id)
        return ExtractStructureResponse(structure=structure).model_dump()

    except Exception as exc:
        logger.error("AI extract_structure failed for doc %s: %s", req.doc_id, exc, exc_info=True)
        return AIFailedResponse(message=str(exc)).model_dump()


@router.post("/extract-structure-async", response_model=StructureTaskDetailResponse, status_code=202)
@limiter.limit("5/minute", key_func=_user_key)
def create_structure_task(
    request: Request,
    req: CreateStructureTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StructureTaskDetailResponse:
    """从文档提取结构（异步模式，适用于大文档）。"""
    # 验证文档归属
    doc = document_service.get_document(db, req.document_id, current_user)

    # 创建任务
    task = StructureTask(
        document_id=req.document_id,
        created_by=current_user.id,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 后台执行
    background_tasks.add_task(structure_service.run_structure_task, db, task.id)

    logger.info("StructureTask %s created for document %s", task.id, req.document_id)
    return StructureTaskDetailResponse(data=StructureTaskResponse.model_validate(task))


@router.get("/structure-task/{task_id}/status", response_model=StructureTaskDetailResponse)
def get_structure_task_status(
    task_id: uuid_lib.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StructureTaskDetailResponse:
    """获取结构识别任务状态。"""
    task = _get_structure_task(db, task_id, current_user)
    return StructureTaskDetailResponse(data=StructureTaskResponse.model_validate(task))


@router.put("/structure/{task_id}", response_model=UpdateStructureResponse)
def update_structure(
    task_id: uuid_lib.UUID,
    req: UpdateStructureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpdateStructureResponse:
    """更新结构数据（用户编辑后保存）。"""
    task = _get_structure_task(db, task_id, current_user)

    # 将 Section 对象转换为字典
    sections_dict = [s.model_dump() if hasattr(s, 'model_dump') else dict(s) for s in req.structure]

    # 更新 edited_structure 字段
    task.edited_structure = {
        "title": req.title or (task.ai_structure.get("title") if task.ai_structure else None),
        "sections": sections_dict,
    }
    db.commit()

    logger.info("StructureTask %s updated by user %s", task_id, current_user.id)
    return UpdateStructureResponse(count=len(req.structure))


@router.post("/structure/{task_id}/find-replace", response_model=UpdateStructureResponse)
def find_and_replace(
    task_id: uuid_lib.UUID,
    req: FindReplaceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UpdateStructureResponse:
    """全局查找替换。"""
    task = _get_structure_task(db, task_id, current_user)

    # 获取当前结构（优先使用 edited_structure，否则使用 ai_structure）
    current_structure = task.edited_structure or task.ai_structure
    if not current_structure or "sections" not in current_structure:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("结构数据")

    sections = current_structure["sections"]
    title = current_structure.get("title", "")

    # 执行查找替换
    count = 0

    def replace_in_text(text: str) -> tuple[str, int]:
        """在文本中查找并替换，返回替换后的文本和替换次数。"""
        if not text:
            return text, 0
        if req.case_sensitive:
            new_text, count = text.replace(req.find, req.replace), text.count(req.find)
        else:
            # 不区分大小写的替换
            import re
            pattern = re.compile(re.escape(req.find), re.IGNORECASE)
            new_text, count = pattern.subn(req.replace, text)
        return new_text, count

    def replace_in_sections(items: list) -> tuple[list, int]:
        """递归遍历并替换章节数据。"""
        nonlocal count
        result = []
        for item in items:
            new_item = dict(item)
            # 替换文本内容
            if "text" in new_item and new_item["text"]:
                new_text, c = replace_in_text(new_item["text"])
                new_item["text"] = new_text
                count += c
            # 递归处理子节点
            if "children" in new_item and new_item["children"]:
                new_item["children"], _ = replace_in_sections(new_item["children"])
            result.append(new_item)
        return result, count

    new_sections, _ = replace_in_sections(sections)

    # 替换标题中的文本
    if title:
        new_title, c = replace_in_text(title)
        title = new_title
        count += c

    # 保存更新后的结构
    task.edited_structure = {
        "title": title,
        "sections": new_sections,
    }
    db.commit()

    logger.info("Find-replace executed on StructureTask %s: %d replacements", task_id, count)
    return UpdateStructureResponse(count=count)


def _get_structure_task(db: Session, task_id: uuid_lib.UUID, current_user: User) -> StructureTask:
    task: StructureTask | None = db.query(StructureTask).filter(StructureTask.id == task_id).first()
    if task is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("结构识别任务")
    if current_user.role != "admin" and task.created_by != current_user.id:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("无权访问此结构识别任务")
    return task


def _read_document_text(file_path: str, file_type: str) -> str:
    """读取文档内容为纯文本，供 AI 处理。"""
    from pathlib import Path  # noqa: PLC0415

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if file_type == "md":
        return path.read_text(encoding="utf-8")

    # docx → 纯文本（保留段落/标题换行，以便 AI 识别结构）
    import mammoth  # noqa: PLC0415
    import re  # noqa: PLC0415

    with path.open("rb") as f:
        result = mammoth.convert_to_html(f)
    html = result.value
    # 1. 先标记表格区域（在去除 HTML 标签前）
    html = re.sub(r"<table[^>]*>", "\n[TABLE_START]\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</table>", "\n[TABLE_END]\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<tr[^>]*>", "\n[ROW_START]\n", html, flags=re.IGNORECASE)
    html = re.sub(r"</tr>", "\n[ROW_END]\n", html, flags=re.IGNORECASE)
    html = re.sub(r"<td[^>]*>", "[CELL_START]", html, flags=re.IGNORECASE)
    html = re.sub(r"</td>", "[CELL_END]\n", html, flags=re.IGNORECASE)
    # 2. 在块级元素闭合标签前插入换行，保留段落分隔
    html = re.sub(r"</(?:p|h[1-6]|li|div|blockquote)>", "\n", html)
    html = re.sub(r"<br\s*/?>", "\n", html)
    # 3. 去除剩余 HTML 标签
    plain = re.sub(r"<[^>]+>", "", html)
    # 4. 合并每行内多余空白，但保留换行
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in plain.splitlines()]
    plain = "\n".join(line for line in lines if line)
    return plain
