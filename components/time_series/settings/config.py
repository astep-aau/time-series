from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


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

    listen_host: str = "0.0.0.0"
    port: int = 8000
    log_level: LogLevel = LogLevel.INFO

    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseSettings

    max_page_size: int = 10000
    default_page_size: int = 100


@lru_cache()
def get_settings():
    return Settings()  # type: ignore
