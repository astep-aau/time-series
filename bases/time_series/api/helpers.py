from typing import Generator

from fastapi import Depends
from sqlmodel import Session
from time_series.database.engine import ENGINE
from time_series.database.unit_of_work import UnitOfWork
from time_series.dataset_service import OverviewService, UploadService


def get_session() -> Generator[Session, None, None]:
    with Session(ENGINE) as session:
        yield session


def get_overview_service(session: Session = Depends(get_session)) -> OverviewService:
    return OverviewService(UnitOfWork(session))


def get_upload_service(session: Session = Depends(get_session)) -> UploadService:
    return UploadService(UnitOfWork(session))
