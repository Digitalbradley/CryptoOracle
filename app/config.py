"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """All application settings, loaded from .env file."""

    # Database
    database_url: str = Field(
        default="postgresql://user:pass@localhost:5432/cryptooracle",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL",
    )

    # Exchange
    exchange_api_key: str = Field(default="", alias="EXCHANGE_API_KEY")
    exchange_api_secret: str = Field(default="", alias="EXCHANGE_API_SECRET")

    # On-chain
    cryptoquant_api_key: str = Field(default="", alias="CRYPTOQUANT_API_KEY")
    glassnode_api_key: str = Field(default="", alias="GLASSNODE_API_KEY")

    # Sentiment
    alternative_me_api: str = Field(
        default="https://api.alternative.me/fng/",
        alias="ALTERNATIVE_ME_API",
    )
    lunarcrush_api_key: str = Field(default="", alias="LUNARCRUSH_API_KEY")

    # News
    newsapi_key: str = Field(default="", alias="NEWSAPI_KEY")
    gnews_api_key: str = Field(default="", alias="GNEWS_API_KEY")

    # Claude API
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # Notifications
    alert_email: str = Field(default="", alias="ALERT_EMAIL")

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Authentication
    jwt_secret_key: str = Field(
        default="CHANGE-ME-IN-PRODUCTION-USE-OPENSSL-RAND-HEX-32",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, alias="JWT_EXPIRY_HOURS")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
