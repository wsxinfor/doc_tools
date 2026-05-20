import logging
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ForbiddenError, NotFoundError
from app.models.template import Template
from app.models.user import User
from app.schemas.template import CreateTemplateRequest, UpdateTemplateRequest

logger = logging.getLogger(__name__)


def list_templates(db: Session) -> list[Template]:
    """模板全公司共享，所有用户可见（不按 created_by 过滤）。"""
    return (
        db.query(Template)
        .filter(Template.is_deleted.is_(False))
        .order_by(Template.created_at.desc())
        .all()  # type: ignore[return-value]
    )


def get_template(db: Session, template_id: uuid.UUID) -> Template:
    tmpl: Template | None = (
        db.query(Template)
        .filter(Template.id == template_id, Template.is_deleted.is_(False))
        .first()
    )
    if tmpl is None:
        raise NotFoundError("模板")
    return tmpl


def create_template(db: Session, req: CreateTemplateRequest, creator: User) -> Template:
    config_dict = req.config.model_dump()
    tmpl = Template(
        name=req.name,
        description=req.description,
        config=config_dict,
        created_by=creator.id,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    logger.info("Created template %s by user %s", tmpl.id, creator.id)
    return tmpl


def update_template(
    db: Session,
    template_id: uuid.UUID,
    req: UpdateTemplateRequest,
    current_user: User,
) -> Template:
    tmpl = get_template(db, template_id)
    _check_can_modify(tmpl, current_user)

    if req.name is not None:
        tmpl.name = req.name
    if req.description is not None:
        tmpl.description = req.description
    if req.config is not None:
        tmpl.config = req.config.model_dump()

    db.commit()
    db.refresh(tmpl)
    return tmpl


def delete_template(
    db: Session,
    template_id: uuid.UUID,
    current_user: User,
) -> Template:
    tmpl = get_template(db, template_id)
    _check_can_modify(tmpl, current_user)
    _check_not_referenced(db, template_id)

    tmpl.is_deleted = True
    db.commit()
    db.refresh(tmpl)
    logger.info("Soft-deleted template %s by user %s", template_id, current_user.id)
    return tmpl


def _check_can_modify(tmpl: Template, current_user: User) -> None:
    if current_user.role != "admin" and tmpl.created_by != current_user.id:
        raise ForbiddenError("只有创建者或管理员可以修改/删除此模板")


def _check_not_referenced(db: Session, template_id: uuid.UUID) -> None:
    """M5 render_tasks 表建立后，校验模板是否被任务引用。"""
    try:
        from app.models.render_task import RenderTask  # type: ignore[attr-defined]  # noqa: PLC0415
        count: int = db.query(RenderTask).filter(RenderTask.template_id == template_id).count()
        if count > 0:
            raise BusinessRuleError(
                "TEMPLATE_IN_USE",
                "模板已被排版任务引用，不可删除",
            )
    except ImportError:
        pass
