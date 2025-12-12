from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class DatabaseSettings(BaseModel):
    username: str
    password: str
    host: str
    port: int = 5432
    name: str
    schema_name: str = "public"

    @property
    def url(self):
        return PostgresDsn(
            "postgresql://%s:%s@%s:%s/%s" % (self.username, self.password, self.host, self.port, self.name)
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", case_sensitive=False)

    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseSettings

    max_page_size: int = 10000
    default_page_size: int = 100


@lru_cache()
def get_settings():
    from pathlib import Path

    env_path = Path(".env")
    print(f"Looking for .env at: {env_path.absolute()}")
    print(f".env exists: {env_path.exists()}")

    return Settings()  # type: ignore
