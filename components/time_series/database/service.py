from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from .engine import engine
from .models import Datapoint, Dataset


class DatasetService:
    """Service for dataset operations"""

    @staticmethod
    def create(name: str, start_date: datetime, description: Optional[str] = None) -> Dataset:
        with Session(engine) as session:
            dataset = Dataset(name=name, start_date=start_date, description=description)
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset

    @staticmethod
    def get_all() -> List[Dataset]:
        with Session(engine) as session:
            return session.exec(select(Dataset)).all()

    @staticmethod
    def get_by_id(dataset_id: int) -> Optional[Dataset]:
        with Session(engine) as session:
            return session.get(Dataset, dataset_id)

    @staticmethod
    def get_by_name(name: str) -> Optional[Dataset]:
        with Session(engine) as session:
            statement = select(Dataset).where(Dataset.name == name)
            return session.exec(statement).first()

    @staticmethod
    def update(dataset_id: int, **kwargs) -> Optional[Dataset]:
        with Session(engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                for key, value in kwargs.items():
                    setattr(dataset, key, value)
                session.add(dataset)
                session.commit()
                session.refresh(dataset)
            return dataset

    @staticmethod
    def delete(dataset_id: int) -> bool:
        with Session(engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False


class DatapointService:
    """Service for datapoint operations"""

    @staticmethod
    def create(dataset_id: int, time: datetime, value: float) -> Datapoint:
        with Session(engine) as session:
            datapoint = Datapoint(dataset_id=dataset_id, time=time, value=value)
            session.add(datapoint)
            session.commit()
            session.refresh(datapoint)
            return datapoint

    @staticmethod
    def bulk_create(datapoints: List[dict]) -> int:
        """Create multiple datapoints at once"""
        with Session(engine) as session:
            for dp_data in datapoints:
                datapoint = Datapoint(**dp_data)
                session.add(datapoint)
            session.commit()
            return len(datapoints)

    @staticmethod
    def get_by_dataset(dataset_id: int) -> List[Datapoint]:
        with Session(engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id).order_by(Datapoint.time)
            return session.exec(statement).all()

    @staticmethod
    def get_range(dataset_id: int, start_time: datetime, end_time: datetime) -> List[Datapoint]:
        with Session(engine) as session:
            statement = (
                select(Datapoint)
                .where(Datapoint.dataset_id == dataset_id, Datapoint.time >= start_time, Datapoint.time <= end_time)
                .order_by(Datapoint.time)
            )
            return session.exec(statement).all()

    @staticmethod
    def delete_before(dataset_id: int, cutoff_time: datetime) -> int:
        """Delete datapoints before cutoff_time"""
        with Session(engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id, Datapoint.time < cutoff_time)
            datapoints = session.exec(statement).all()
            count = len(datapoints)

            for dp in datapoints:
                session.delete(dp)

            session.commit()
            return count
