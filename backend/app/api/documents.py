import uuid

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import BusinessRuleError
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentDetailResponse, DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentDetailResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    """上传文件文档（docx/md/txt）"""
    doc = await document_service.upload_document(db, file, current_user)
    return DocumentDetailResponse(data=DocumentResponse.model_validate(doc))


@router.post("", response_model=DocumentDetailResponse, status_code=201)
def create_document(
    req: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    """创建文本文档（粘贴文本模式）

    支持 Markdown 和纯文本，自动检测格式。
    文本长度限制：50000 字符
    """
    # 验证文本长度
    if req.source_type == "text":
        if not req.content:
            raise HTTPException(status_code=422, detail="text 模式必须提供 content 字段")
        if len(req.content) > 50000:
            raise HTTPException(status_code=422, detail="文本长度不能超过 50000 字符")

    doc = document_service.create_document_from_text(
        db,
        filename=req.filename,
        file_type=req.file_type,
        source_type=req.source_type,
        content=req.content,
        file_size=req.file_size or len(req.content) if req.content else 0,
        user=current_user
    )
    return DocumentDetailResponse(data=DocumentResponse.model_validate(doc))


@router.get("", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    docs = document_service.list_documents(db, current_user)
    return DocumentListResponse(data=[DocumentResponse.model_validate(d) for d in docs])


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    doc = document_service.get_document(db, doc_id, current_user)
    return DocumentDetailResponse(data=DocumentResponse.model_validate(doc))


@router.delete("/{doc_id}", response_model=DocumentDetailResponse)
def delete_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    doc = document_service.delete_document(db, doc_id, current_user)
    return DocumentDetailResponse(data=DocumentResponse.model_validate(doc))
