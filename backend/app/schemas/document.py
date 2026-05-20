import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    """创建文档请求（支持文件上传或文本提交）"""
    filename: str
    file_type: Literal["docx", "md", "txt"]
    source_type: Literal["file", "text"] = "file"
    content: Optional[str] = None  # text 模式时必填，最大 50000 字符
    file_size: int = 0

    model_config = {"json_schema_extra": {
        "example": {
            "filename": "example.md",
            "file_type": "md",
            "source_type": "text",
            "content": "# 标题\n\n这是正文内容...",
            "file_size": 0
        }
    }}


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_path: Optional[str] = None
    file_type: str
    source_type: str
    content: Optional[str] = None
    file_size: int
    uploader_id: uuid.UUID
    is_deleted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    data: list[DocumentResponse]
    message: str = "ok"


class DocumentDetailResponse(BaseModel):
    data: DocumentResponse
    message: str = "ok"

