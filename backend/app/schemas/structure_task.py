import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.ai import Section


class StructureTaskResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    ai_structure: Optional[dict]
    edited_structure: Optional[dict]
    error_message: Optional[str]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StructureTaskListResponse(BaseModel):
    data: list[StructureTaskResponse]
    message: str = "ok"


class StructureTaskDetailResponse(BaseModel):
    data: StructureTaskResponse
    message: str = "ok"


class CreateStructureTaskRequest(BaseModel):
    document_id: uuid.UUID


class UpdateStructureRequest(BaseModel):
    """更新结构数据的请求."""
    structure: list[Section] = Field(description="编辑后的结构数据")
    title: Optional[str] = Field(default=None, description="文档标题（可选）")


class FindReplaceRequest(BaseModel):
    """查找替换请求."""
    find: str = Field(description="要查找的文本")
    replace: str = Field(description="替换为的文本")
    case_sensitive: bool = Field(default=False, description="是否区分大小写")
    replace_all: bool = Field(default=True, description="是否全部替换")


class UpdateStructureResponse(BaseModel):
    """更新结构响应."""
    status: str = "ok"
    message: str = "结构已更新"
    count: int = Field(description="更新的节点数量")
