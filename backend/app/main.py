import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import auth, admin_users, documents, ai_process, admin_settings, templates, render
from app.api.ai_process import limiter
from app.core.exceptions import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
)

app = FastAPI(title="DocFormat API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(documents.router)
app.include_router(ai_process.router)
app.include_router(admin_settings.router)
app.include_router(templates.router)
app.include_router(render.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
