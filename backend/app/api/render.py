import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models.render_task import RenderTask
from app.models.user import User
from app.schemas.render import (
    CreateRenderRequest,
    RenderTaskDetailResponse,
    RenderTaskListResponse,
    RenderTaskResponse,
)
from app.services import render_service

router = APIRouter(prefix="/api/render", tags=["render"])


@router.post("", response_model=RenderTaskDetailResponse, status_code=202)
def create_render_task(
    req: CreateRenderRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RenderTaskDetailResponse:
    # 将 render_params 合并到 ai_structure 中一起存储（方便后台任务读取）
    structure_with_params = dict(req.ai_structure)
    structure_with_params["render_params"] = req.render_params

    task = RenderTask(
        document_id=req.document_id,
        template_id=req.template_id,
        ai_clean_result=req.ai_clean_result,
        ai_structure=structure_with_params,
        created_by=current_user.id,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 异步后台执行排版
    background_tasks.add_task(render_service.run_render_task, db, task.id)

    return RenderTaskDetailResponse(data=RenderTaskResponse.model_validate(task))


@router.get("/{task_id}/status", response_model=RenderTaskDetailResponse)
def get_task_status(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RenderTaskDetailResponse:
    task = _get_task(db, task_id, current_user)
    return RenderTaskDetailResponse(data=RenderTaskResponse.model_validate(task))


@router.get("", response_model=RenderTaskListResponse)
def list_render_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RenderTaskListResponse:
    q = db.query(RenderTask)
    if current_user.role != "admin":
        q = q.filter(RenderTask.created_by == current_user.id)
    tasks = q.order_by(RenderTask.created_at.desc()).all()
    return RenderTaskListResponse(data=[RenderTaskResponse.model_validate(t) for t in tasks])


@router.get("/{task_id}/preview", response_class=HTMLResponse)
def preview_render_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    task = _get_task(db, task_id, current_user)
    if task.status != "done":
        raise BusinessRuleError("RENDER_NOT_DONE", "排版任务尚未完成，无法预览")
    if not task.preview_path:
        raise BusinessRuleError("PREVIEW_NOT_FOUND", "预览文件不存在")
    from pathlib import Path  # noqa: PLC0415
    p = Path(task.preview_path)
    if not p.exists():
        raise BusinessRuleError("PREVIEW_NOT_FOUND", "预览文件不存在")
    return HTMLResponse(content=p.read_text(encoding="utf-8"))


@router.get("/{task_id}/download")
def download_render_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    task = _get_task(db, task_id, current_user)
    if task.status != "done":
        raise BusinessRuleError("RENDER_NOT_DONE", "排版任务尚未完成，无法下载")
    if not task.result_path:
        raise BusinessRuleError("RESULT_NOT_FOUND", "输出文件不存在")
    from pathlib import Path  # noqa: PLC0415
    p = Path(task.result_path)
    if not p.exists():
        raise BusinessRuleError("RESULT_NOT_FOUND", "输出文件不存在")
    filename = p.name
    return FileResponse(
        path=str(p),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


def _get_task(db: Session, task_id: uuid.UUID, current_user: User) -> RenderTask:
    task: RenderTask | None = db.query(RenderTask).filter(RenderTask.id == task_id).first()
    if task is None:
        raise NotFoundError("排版任务")
    if current_user.role != "admin" and task.created_by != current_user.id:
        raise ForbiddenError("无权访问此排版任务")
    return task
