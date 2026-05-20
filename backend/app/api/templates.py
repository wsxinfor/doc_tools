import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.template import (
    CreateTemplateRequest,
    TemplateDetailResponse,
    TemplateListResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)
from app.services import template_service

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=TemplateListResponse)
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateListResponse:
    templates = template_service.list_templates(db)
    return TemplateListResponse(data=[TemplateResponse.model_validate(t) for t in templates])


@router.post("", response_model=TemplateDetailResponse, status_code=201)
def create_template(
    req: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateDetailResponse:
    tmpl = template_service.create_template(db, req, current_user)
    return TemplateDetailResponse(data=TemplateResponse.model_validate(tmpl))


@router.get("/{template_id}", response_model=TemplateDetailResponse)
def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateDetailResponse:
    tmpl = template_service.get_template(db, template_id)
    return TemplateDetailResponse(data=TemplateResponse.model_validate(tmpl))


@router.put("/{template_id}", response_model=TemplateDetailResponse)
def update_template(
    template_id: uuid.UUID,
    req: UpdateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateDetailResponse:
    tmpl = template_service.update_template(db, template_id, req, current_user)
    return TemplateDetailResponse(data=TemplateResponse.model_validate(tmpl))


@router.delete("/{template_id}", response_model=TemplateDetailResponse)
def delete_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateDetailResponse:
    tmpl = template_service.delete_template(db, template_id, current_user)
    return TemplateDetailResponse(data=TemplateResponse.model_validate(tmpl))
