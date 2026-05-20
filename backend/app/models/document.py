import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)  # text 模式为 None
    file_type: Mapped[str] = mapped_column(String(8), nullable=False)  # 'docx' | 'md' | 'txt'
    source_type: Mapped[str] = mapped_column(String(8), nullable=False, default="file")  # 'file' | 'text'
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # text 模式的原始内容
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
