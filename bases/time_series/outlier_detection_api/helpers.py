from typing import Generator

from sqlmodel import Session
from time_series.database.engine import get_engine


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session
