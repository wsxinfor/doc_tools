import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateRenderRequest(BaseModel):
    document_id: uuid.UUID
    template_id: uuid.UUID
    ai_clean_result: str = ""  # 已废弃，后端现在从 ai_structure 提取正文
    ai_structure: dict[str, object]
    render_params: dict[str, object]  # cover fields: client_name, project_name, doc_version, date


class RenderTaskResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    template_id: uuid.UUID
    status: str
    result_path: Optional[str]
    preview_path: Optional[str]
    error_message: Optional[str]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RenderTaskListResponse(BaseModel):
    data: list[RenderTaskResponse]
    message: str = "ok"


class RenderTaskDetailResponse(BaseModel):
    data: RenderTaskResponse
    message: str = "ok"
