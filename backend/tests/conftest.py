"""pytest fixtures：测试数据库 + TestClient。

测试数据库通过 DATABASE_URL_TEST 独立配置。
每个测试用例独立 setup / teardown，不依赖残留数据。
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# 必须在 import app 之前设置环境变量，避免 config.py 读取 .env
os.environ.setdefault("DATABASE_URL", "postgresql://docformat_user:docformat_pass@localhost:5433/docformat")
os.environ.setdefault("DATABASE_URL_TEST", "postgresql://docformat_user:docformat_pass@localhost:5433/docformat_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("APP_ENV", "test")

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models import user as _user_model  # noqa: F401  # 确保 create_all 能感知 User 表
from app.models import document as _document_model  # noqa: F401  # Document 表
from app.models import system_config as _system_config_model  # noqa: F401  # SystemConfig 表
from app.models import template as _template_model  # noqa: F401  # Template 表
from app.models import render_task as _render_task_model  # noqa: F401  # RenderTask 表
from app.main import app as fastapi_app  # noqa: E402
from app.api.deps import get_db  # noqa: E402

TEST_DB_URL = settings.DATABASE_URL_TEST or settings.DATABASE_URL

test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables() -> None:
    """在测试库上建表（session 级别，只跑一次）。"""
    Base.metadata.create_all(bind=test_engine)
    yield  # type: ignore[misc]
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db() -> Session:
    """每个测试用例独立事务，测试后回滚。"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db: Session) -> TestClient:
    """替换 get_db 依赖，让 TestClient 使用测试数据库。"""
    def override_get_db() -> Session:
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app, raise_server_exceptions=False) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
