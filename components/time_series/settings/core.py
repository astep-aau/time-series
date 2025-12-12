from enum import IntEnum

from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(IntEnum):
    DEVELOPMENT = 0
    PRODUCTION = 1


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
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: Environment = Environment.DEVELOPMENT
    database: DatabaseSettings

    max_page_size: int = 10000
    default_page_size: int = 100


settings = Settings()  # type: ignore
