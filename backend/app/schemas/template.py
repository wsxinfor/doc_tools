import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FontConfig(BaseModel):
    model_config = {"extra": "allow"}

    cn_font: str = "Song Ti"
    en_font: str = "Times New Roman"
    size: float = 12
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str = "#000000"


class SpacingConfig(BaseModel):
    model_config = {"extra": "allow"}

    before: int = 0
    after: int = 0
    line: float = 1.5


class MarginConfig(BaseModel):
    model_config = {"extra": "allow"}

    top: float = 2.54
    bottom: float = 2.54
    left: float = 3.17
    right: float = 3.17


class HeadingConfig(BaseModel):
    model_config = {"extra": "allow"}

    font: FontConfig = Field(default_factory=FontConfig)
    spacing: SpacingConfig = Field(default_factory=SpacingConfig)
    alignment: Literal["left", "center", "right"] = "left"
    numbering_style: Literal["none", "chapter-arabic", "chapter-chinese", "cn-number", "arabic-number", "decimal"] = "none"
    page_break_before: bool = False


class CoverFieldConfig(BaseModel):
    model_config = {"extra": "allow"}

    text_placeholder: str = ""
    font: FontConfig = Field(default_factory=FontConfig)
    position: str = "center"


class CoverConfig(BaseModel):
    model_config = {"extra": "allow"}

    client_name: CoverFieldConfig = Field(default_factory=CoverFieldConfig)
    project_name: CoverFieldConfig = Field(default_factory=CoverFieldConfig)
    doc_version: CoverFieldConfig = Field(default_factory=CoverFieldConfig)
    company_name: CoverFieldConfig = Field(default_factory=CoverFieldConfig)
    date: CoverFieldConfig = Field(default_factory=CoverFieldConfig)
    bg_color: str = "#FFFFFF"
    logo_path: Optional[str] = None
    logo_position: Optional[str] = None


class HeaderFooterConfig(BaseModel):
    model_config = {"extra": "allow"}

    header_left: str = ""
    header_center: str = ""
    header_right: str = ""
    footer_left: str = ""
    footer_center: str = ""
    footer_right: str = ""
    show_divider: bool = True
    divider_color: str = "#CCCCCC"
    font: FontConfig = Field(default_factory=FontConfig)
    first_page_hide: bool = True


class TocConfig(BaseModel):
    model_config = {"extra": "allow"}

    max_level: int = 3
    title_text: str = "目  录"
    title_font: FontConfig = Field(default_factory=lambda: FontConfig(cn_font="宋体", en_font="Times New Roman", size=14, bold=True, color="#000000"))
    entry_font: FontConfig = Field(default_factory=FontConfig)
    show_page_number: bool = True
    separate_page: bool = True


class BodyConfig(BaseModel):
    model_config = {"extra": "allow"}

    font: FontConfig = Field(default_factory=FontConfig)
    spacing: SpacingConfig = Field(default_factory=SpacingConfig)
    first_line_indent: int = 2
    margins: MarginConfig = Field(default_factory=MarginConfig)
    list_style: str = "none"  # "none" | "triangle" | "diamond" | "circle" | "hollow_diamond" | "square" | "dot"


class TableConfig(BaseModel):
    model_config = {"extra": "allow"}

    # 表头配置
    header_font: FontConfig = Field(default_factory=lambda: FontConfig(cn_font="SimSun", en_font="Times New Roman", size=12, color="#000000"))
    header_bg_color: str = "#D6E7F5"
    header_alignment: Literal["left", "center", "right"] = "center"
    header_v_alignment: Literal["top", "center", "bottom"] = "center"

    # 表体配置
    body_font: FontConfig = Field(default_factory=lambda: FontConfig(cn_font="FangSong", en_font="Times New Roman", size=12, color="#000000"))
    body_alignment: Literal["left", "center", "right"] = "left"
    body_v_alignment: Literal["top", "center", "bottom"] = "center"

    # 首列特殊配置（可选）
    first_col_font: FontConfig = Field(default_factory=FontConfig)
    first_col_alignment: Literal["left", "center", "right"] = "center"

    # 边框配置
    border_color: str = "auto"
    border_width_outer: int = 12  # 1.5pt (单位 1/8pt)
    border_width_inner: int = 4   # 0.5pt

    # 布局配置
    column_widths: list[float] = Field(default_factory=list)  # 空列表=自适应
    repeat_header: bool = True


class FigureConfig(BaseModel):
    model_config = {"extra": "allow"}

    image_alignment: Literal["left", "center", "right"] = "center"
    caption_font: FontConfig = Field(default_factory=FontConfig)
    caption_style: Literal["simple", "chapter-figure"] = "simple"  # simple=图 1, chapter-figure=图 1-1
    table: TableConfig = Field(default_factory=TableConfig)


class TemplateConfig(BaseModel):
    model_config = {"extra": "allow"}

    cover: CoverConfig = Field(default_factory=CoverConfig)
    header_footer: HeaderFooterConfig = Field(default_factory=HeaderFooterConfig)
    headings: dict[str, HeadingConfig] = Field(
        default_factory=lambda: {
            "h1": HeadingConfig(),
            "h2": HeadingConfig(),
            "h3": HeadingConfig(),
            "h4": HeadingConfig(),
        }
    )
    toc: TocConfig = Field(default_factory=TocConfig)
    body: BodyConfig = Field(default_factory=BodyConfig)
    figure: FigureConfig = Field(default_factory=FigureConfig)


class CreateTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    config: TemplateConfig = Field(default_factory=TemplateConfig)


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = None
    config: Optional[TemplateConfig] = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    config: dict
    created_by: uuid.UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    data: list[TemplateResponse]
    message: str = "ok"


class TemplateDetailResponse(BaseModel):
    data: TemplateResponse
    message: str = "ok"
