from functools import lru_cache

from sqlmodel import create_engine
from time_series.settings import get_settings


@lru_cache
def get_engine():
    settings = get_settings()

    return create_engine(
        str(settings.database.url),
        echo=(settings.environment != "production"),
    )
