"""Налаштування API: змінні середовища з префіксом PORTAL_ або файл .env."""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Налаштування FastAPI-застосунку."""

    model_config = SettingsConfigDict(
        env_prefix="PORTAL_",
        env_file=".env",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///db.sqlite3"
    api_key: SecretStr = Field(min_length=16)
    echo_sql: bool = False
