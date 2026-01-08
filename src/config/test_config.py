from pydantic_settings import BaseSettings
from typing import Optional


class TestSettings(BaseSettings):
    # Database settings - using SQLite for testing
    database_url: str = "sqlite:///./test.db"

    # JWT settings
    jwt_secret_key: str = "test-secret-key-for-testing-purposes-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application settings
    app_name: str = "Todo Fullstack App - Test"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Create a test settings instance
test_settings = TestSettings()