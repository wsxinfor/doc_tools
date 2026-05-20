import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Section(BaseModel):
    """文档段落/章节结构."""
    level: int = Field(description="标题层级 (0=正文)")
    text: str = Field(description="文本内容")
    paragraph_type: Literal['heading', 'body', 'table', 'image'] = Field(description="段落类型")
    children: list['Section'] = Field(default_factory=list, description="子节点")
    table_data: Optional[dict] = Field(default=None, description="表格数据")
    image_path: Optional[str] = Field(default=None, description="图片路径")


class CleanRequest(BaseModel):
    doc_id: uuid.UUID


class ExtractStructureRequest(BaseModel):
    doc_id: uuid.UUID
    # cleaned_text 字段已废弃，后端现在直接从 DOCX 提取


class CleanResponse(BaseModel):
    status: str = "ok"
    cleaned_text: str
    original_text: str = ""
    message: str = "ok"


class ExtractStructureResponse(BaseModel):
    status: str = "ok"
    structure: dict[str, object]
    message: str = "ok"


class AIFailedResponse(BaseModel):
    status: str = "ai_failed"
    message: str = "AI 处理未成功，请手动调整后继续"
    original_text: str = ""


class UpdateAISettingsRequest(BaseModel):
    provider: Literal["qwen", "openai"]
    api_key: str = Field(min_length=1)
    model_url: str = Field(default="")   # 模型 base URL，空字符串表示使用默认
    model_name: str = Field(default="")  # 模型名称，空字符串表示使用默认


class AISettingsResponse(BaseModel):
    provider: str
    has_api_key: bool  # 不返回 key 本身
    model_url: str = ""
    model_name: str = ""
    message: str = "ok"


class AITestResponse(BaseModel):
    ok: bool
    message: str
