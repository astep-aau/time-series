from functools import lru_cache

from sqlmodel import create_engine
from time_series.settings import get_database_settings


@lru_cache
def get_engine():
    return create_engine(str(get_database_settings().url))
