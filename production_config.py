"""
Production configuration for the Todo Fullstack App backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field


class ProductionSettings(BaseSettings):
    # Database settings
    database_url: str = Field(
        default=...,
        description="Database connection string for production"
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQL query logging (should be False in production)"
    )

    # JWT settings
    jwt_secret_key: str = Field(
        default=...,
        description="Secret key for JWT encoding/decoding (must be set in production)"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT encoding"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes"
    )

    # Application settings
    app_name: str = Field(
        default="Todo Fullstack App - Production",
        description="Name of the application"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode (should be False in production)"
    )
    api_v1_prefix: str = Field(
        default="/api/v1",
        description="API version prefix"
    )

    # CORS settings
    backend_cors_origins: str = Field(
        default=...,
        description="Comma-separated list of allowed origins (must be set in production)"
    )

    # Security settings
    allowed_hosts: str = Field(
        default=...,
        description="Comma-separated list of allowed hosts (must be set in production)"
    )
    max_login_attempts: int = Field(
        default=5,
        description="Maximum login attempts before rate limiting"
    )
    password_min_length: int = Field(
        default=8,
        description="Minimum password length"
    )

    # Rate limiting settings
    rate_limit_auth_register: str = Field(
        default="5/hour",
        description="Rate limit for registration"
    )
    rate_limit_auth_login: str = Field(
        default="10/15minutes",
        description="Rate limit for login"
    )
    rate_limit_auth_logout: str = Field(
        default="20/minute",
        description="Rate limit for logout"
    )
    rate_limit_auth_validate_token: str = Field(
        default="30/minute",
        description="Rate limit for token validation"
    )
    rate_limit_auth_profile: str = Field(
        default="100/minute",
        description="Rate limit for profile access"
    )

    # Pagination settings
    default_page_size: int = Field(
        default=20,
        description="Default number of items per page"
    )
    max_page_size: int = Field(
        default=100,
        description="Maximum number of items per page"
    )

    model_config = {"env_file": ".env.prod", "env_file_encoding": "utf-8"}

    @property
    def cors_origins(self) -> List[str]:
        """Return CORS origins as a list"""
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]


# Create a settings instance
production_settings = ProductionSettings()