from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # 数据库
    DATABASE_URL: str
    DATABASE_URL_TEST: str = ""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # AI 服务
    AI_PROVIDER: Literal["qwen", "openai"] = "qwen"
    QWEN_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # 文件存储
    UPLOAD_DIR: str = "./storage/uploads"
    OUTPUT_DIR: str = "./storage/outputs"
    MAX_FILE_SIZE_MB: int = 20

    # 应用
    DEFAULT_COMPANY_NAME: str = "北京昱华源码科技有限公司"
    APP_ENV: Literal["development", "production", "test"] = "development"

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL 必须是有效的 PostgreSQL 连接字符串")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_must_not_be_placeholder(cls, v: str) -> str:
        if not v or v == "your-secret-key-here":
            raise ValueError("JWT_SECRET_KEY 未配置，请在 .env 中设置真实密钥")
        return v

    @model_validator(mode="after")
    def ai_provider_key_must_exist(self) -> "Settings":
        if self.APP_ENV == "production":
            if self.AI_PROVIDER == "qwen" and not self.QWEN_API_KEY:
                raise ValueError("AI_PROVIDER=qwen 时，QWEN_API_KEY 不能为空")
            if self.AI_PROVIDER == "openai" and not self.OPENAI_API_KEY:
                raise ValueError("AI_PROVIDER=openai 时，OPENAI_API_KEY 不能为空")
        return self


settings = Settings()  # type: ignore[call-arg]  # pydantic-settings 从 env 读取，mypy 无法感知
