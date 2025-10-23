from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, col, select

from .engine import engine as default_engine
from .models import Datapoint, Dataset


class DatasetRepository:
    """Repository for dataset operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(self, name: str, start_date: datetime, description: Optional[str] = None) -> Dataset:
        with Session(self.engine) as session:
            dataset = Dataset(name=name, start_date=start_date, description=description)
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset

    def get_all(self) -> List[Dataset]:
        with Session(self.engine) as session:
            return list(session.exec(select(Dataset)).all())

    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        with Session(self.engine) as session:
            return session.get(Dataset, dataset_id)

    def get_by_name(self, name: str) -> Optional[Dataset]:
        with Session(self.engine) as session:
            statement = select(Dataset).where(Dataset.name == name)
            return session.exec(statement).first()

    def update(self, dataset_id: int, **kwargs) -> Optional[Dataset]:
        with Session(self.engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                for key, value in kwargs.items():
                    setattr(dataset, key, value)
                session.add(dataset)
                session.commit()
                session.refresh(dataset)
            return dataset

    def delete(self, dataset_id: int) -> bool:
        with Session(self.engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False


class DatapointRepository:
    """Repository for datapoint operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(self, dataset_id: int, time: datetime, value: float) -> Datapoint:
        with Session(self.engine) as session:
            datapoint = Datapoint(dataset_id=dataset_id, time=time, value=value)
            session.add(datapoint)
            session.commit()
            session.refresh(datapoint)
            return datapoint

    def bulk_create(self, datapoints: List[dict]) -> int:
        """Create multiple datapoints at once"""
        with Session(self.engine) as session:
            for dp_data in datapoints:
                datapoint = Datapoint(**dp_data)
                session.add(datapoint)
            session.commit()
            return len(datapoints)

    def get_by_dataset(self, dataset_id: int) -> List[Datapoint]:
        with Session(self.engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id).order_by(col(Datapoint.time))
            return list(session.exec(statement).all())

    def get_range(self, dataset_id: int, start_time: datetime, end_time: datetime) -> List[Datapoint]:
        with Session(self.engine) as session:
            statement = (
                select(Datapoint)
                .where(Datapoint.dataset_id == dataset_id, Datapoint.time >= start_time, Datapoint.time <= end_time)
                .order_by(col(Datapoint.time))
            )
            return list(session.exec(statement).all())

    def delete_before(self, dataset_id: int, cutoff_time: datetime) -> int:
        """Delete datapoints before cutoff_time"""
        with Session(self.engine) as session:
            statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id, Datapoint.time < cutoff_time)
            datapoints = session.exec(statement).all()
            count = len(datapoints)

            for dp in datapoints:
                session.delete(dp)

            session.commit()
            return count
