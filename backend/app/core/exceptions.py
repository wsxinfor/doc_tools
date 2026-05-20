import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, detail: Any = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} 不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ForbiddenError(AppError):
    def __init__(self, message: str = "无操作权限") -> None:
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class UnauthorizedError(AppError):
    def __init__(self, message: str = "未认证或 Token 无效") -> None:
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class BusinessRuleError(AppError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("AppError %s: %s", exc.code, exc.message, exc_info=exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on %s %s", request.method, request.url, exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": "INTERNAL_ERROR", "message": "服务器内部错误", "detail": None},
        )
