from typing import Generator

from fastapi import Depends
from sqlmodel import Session
from time_series.database.engine import get_engine
from time_series.database.unit_of_work import UnitOfWork
from time_series.forecasting.data_service import forecastingService


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def get_forecasting_service(session: Session = Depends(get_session)) -> forecastingService:
    return forecastingService(UnitOfWork(session))
