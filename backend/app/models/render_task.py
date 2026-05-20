import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RenderTask(Base):
    __tablename__ = "render_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # 'pending' | 'processing' | 'done' | 'failed'
    ai_clean_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_structure: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    result_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    preview_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
