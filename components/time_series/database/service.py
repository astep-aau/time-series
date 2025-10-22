from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, col, select

from .engine import engine as default_engine
from .models import Datapoint, Dataset


class DatasetService:
    """Service for dataset operations"""

    @staticmethod
    def create(name: str, start_date: datetime, description: Optional[str] = None, engine=None) -> Dataset:
        _engine = engine or default_engine
        with Session(_engine) as session:
            dataset = Dataset(name=name, start_date=start_date, description=description)
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset

    @staticmethod
    def get_all(engine=None) -> List[Dataset]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            return list(session.exec(select(Dataset)).all())

    @staticmethod
    def get_by_id(dataset_id: int, engine=None) -> Optional[Dataset]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            return session.get(Dataset, dataset_id)

    @staticmethod
    def get_by_name(name: str, engine=None) -> Optional[Dataset]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            statement = select(Dataset).where(Dataset.name == name)
            return session.exec(statement).first()

    @staticmethod
    def update(dataset_id: int, engine=None, **kwargs) -> Optional[Dataset]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                for key, value in kwargs.items():
                    setattr(dataset, key, value)
                session.add(dataset)
                session.commit()
                session.refresh(dataset)
            return dataset

    @staticmethod
    def delete(dataset_id: int, engine=None) -> bool:
        _engine = engine or default_engine
        with Session(_engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False


class DatapointService:
    """Service for datapoint operations"""

    @staticmethod
    def create(dataset_id: int, time: datetime, value: float, engine=None) -> Datapoint:
        _engine = engine or default_engine
        with Session(_engine) as session:
            datapoint = Datapoint(dataset_id=dataset_id, time=time, value=value)
            session.add(datapoint)
            session.commit()
            session.refresh(datapoint)
            return datapoint

    @staticmethod
    def bulk_create(datapoints: List[dict], engine=None) -> int:
        """Create multiple datapoints at once"""
        _engine = engine or default_engine
        with Session(_engine) as session:
            for dp_data in datapoints:
                datapoint = Datapoint(**dp_data)
                session.add(datapoint)
            session.commit()
            return len(datapoints)

    @staticmethod
    def get_by_dataset(dataset_id: int, engine=None) -> List[Datapoint]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id).order_by(col(Datapoint.time))
            return list(session.exec(statement).all())

    @staticmethod
    def get_range(dataset_id: int, start_time: datetime, end_time: datetime, engine=None) -> List[Datapoint]:
        _engine = engine or default_engine
        with Session(_engine) as session:
            statement = (
                select(Datapoint)
                .where(Datapoint.dataset_id == dataset_id, Datapoint.time >= start_time, Datapoint.time <= end_time)
                .order_by(col(Datapoint.time))
            )
            return list(session.exec(statement).all())

    @staticmethod
    def delete_before(dataset_id: int, cutoff_time: datetime, engine=None) -> int:
        """Delete datapoints before cutoff_time"""
        _engine = engine or default_engine
        with Session(_engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id, Datapoint.time < cutoff_time)
            datapoints = session.exec(statement).all()
            count = len(datapoints)

            for dp in datapoints:
                session.delete(dp)

            session.commit()
            return count
