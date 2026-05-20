import asyncio
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.ai import AISettingsResponse, AITestResponse, UpdateAISettingsRequest
from app.services import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/settings", tags=["admin"])


@router.get("/ai", response_model=AISettingsResponse)
def get_ai_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AISettingsResponse:
    info = ai_service.get_ai_settings(db)
    return AISettingsResponse(
        provider=str(info["provider"]),
        has_api_key=bool(info["has_api_key"]),
        model_url=str(info.get("model_url", "")),
        model_name=str(info.get("model_name", "")),
    )


@router.put("/ai", response_model=AISettingsResponse)
def update_ai_settings(
    req: UpdateAISettingsRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AISettingsResponse:
    ai_service.update_ai_settings(
        db,
        provider=req.provider,
        api_key=req.api_key,
        model_url=req.model_url,
        model_name=req.model_name,
    )
    return AISettingsResponse(
        provider=req.provider,
        has_api_key=True,
        model_url=req.model_url,
        model_name=req.model_name,
    )


@router.post("/ai/test", response_model=AITestResponse)
async def test_ai_settings(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> AITestResponse:
    """用当前保存的配置发送一条最小测试请求，验证连通性。"""
    try:
        adapter = ai_service._get_adapter(db)  # noqa: SLF001
        result = await asyncio.wait_for(adapter.clean_text("hi"), timeout=10.0)
        logger.info("AI test succeeded, response length=%d", len(str(result)))
        return AITestResponse(ok=True, message="连接成功")
    except asyncio.TimeoutError:
        return AITestResponse(ok=False, message="连接超时（10s），请检查模型地址和网络")
    except Exception as exc:
        logger.warning("AI test failed: %s", exc)
        return AITestResponse(ok=False, message=str(exc))
