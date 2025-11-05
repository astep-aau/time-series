from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, col, select

from .engine import engine as default_engine
from .models import Analysis, Anomaly, AnomalyType, Datapoint, Dataset


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
            datapoint = Datapoint(dataset_id=dataset_id, time=time, value=float(value))
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


class AnalysisRepository:
    """Repository for analysis operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(
        self,
        dataset_id: int,
        model: str,
        name: str,
        description: Optional[str] = None,
    ) -> Analysis:
        """Create a new analysis"""
        with Session(self.engine) as session:
            analysis = Analysis(
                dataset_id=dataset_id,
                model=model,
                name=name,
                description=description,
            )
            session.add(analysis)
            session.commit()
            session.refresh(analysis)
            return analysis

    def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """Get an analysis by its ID"""
        with Session(self.engine) as session:
            return session.get(Analysis, analysis_id)

    def get_by_dataset(self, dataset_id: int) -> List[Analysis]:
        """Get all analyses for a dataset"""
        with Session(self.engine) as session:
            statement = select(Analysis).where(Analysis.dataset_id == dataset_id).order_by(col(Analysis.id))
            return list(session.exec(statement).all())

    def update(self, analysis_id: int, **kwargs) -> Optional[Analysis]:
        """Update an analysis"""
        with Session(self.engine) as session:
            analysis = session.get(Analysis, analysis_id)
            if analysis:
                for key, value in kwargs.items():
                    setattr(analysis, key, value)
                session.add(analysis)
                session.commit()
                session.refresh(analysis)
            return analysis

    def delete(self, analysis_id: int) -> bool:
        """Delete an analysis"""
        with Session(self.engine) as session:
            analysis = session.get(Analysis, analysis_id)
            if analysis:
                session.delete(analysis)
                session.commit()
                return True
            return False


class AnomalyRepository:
    """Repository for anomaly operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(
        self,
        analysis_id: int,
        start: datetime,
        end: datetime,
        type: AnomalyType,
        validated: bool = False,
    ) -> Anomaly:
        """Create a new anomaly"""
        with Session(self.engine) as session:
            anomaly = Anomaly(
                analysis_id=analysis_id,
                start=start,
                end=end,
                type=type,
                validated=validated,
            )
            session.add(anomaly)
            session.commit()
            session.refresh(anomaly)
            return anomaly

    def bulk_create(self, anomalies: List[dict]) -> int:
        """Create multiple anomalies at once"""
        with Session(self.engine) as session:
            for anomaly_data in anomalies:
                anomaly = Anomaly(**anomaly_data)
                session.add(anomaly)
            session.commit()
            return len(anomalies)

    def get_by_id(self, anomaly_id: int) -> Optional[Anomaly]:
        """Get an anomaly by its ID"""
        with Session(self.engine) as session:
            return session.get(Anomaly, anomaly_id)

    def get_by_analysis(self, analysis_id: int) -> List[Anomaly]:
        """Get all anomalies for an analysis"""
        with Session(self.engine) as session:
            statement = select(Anomaly).where(Anomaly.analysis_id == analysis_id).order_by(col(Anomaly.start))
            return list(session.exec(statement).all())

    def get_by_type(self, analysis_id: int, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Get anomalies of a specific type for an analysis"""
        with Session(self.engine) as session:
            statement = (
                select(Anomaly)
                .where(Anomaly.analysis_id == analysis_id, Anomaly.type == anomaly_type)
                .order_by(col(Anomaly.start))
            )
            return list(session.exec(statement).all())

    def get_validated(self, analysis_id: int, validated: bool = True) -> List[Anomaly]:
        """Get validated or unvalidated anomalies for an analysis"""
        with Session(self.engine) as session:
            statement = (
                select(Anomaly)
                .where(Anomaly.analysis_id == analysis_id, Anomaly.validated == validated)
                .order_by(col(Anomaly.start))
            )
            return list(session.exec(statement).all())

    def get_range(self, analysis_id: int, start_time: datetime, end_time: datetime) -> List[Anomaly]:
        """Get anomalies that overlap with a time range"""
        with Session(self.engine) as session:
            statement = (
                select(Anomaly)
                .where(
                    Anomaly.analysis_id == analysis_id,
                    Anomaly.start <= end_time,
                    Anomaly.end >= start_time,
                )
                .order_by(col(Anomaly.start))
            )
            return list(session.exec(statement).all())

    def update(self, anomaly_id: int, **kwargs) -> Optional[Anomaly]:
        """Update an anomaly"""
        with Session(self.engine) as session:
            anomaly = session.get(Anomaly, anomaly_id)
            if anomaly:
                for key, value in kwargs.items():
                    setattr(anomaly, key, value)
                session.add(anomaly)
                session.commit()
                session.refresh(anomaly)
            return anomaly

    def validate(self, anomaly_id: int) -> Optional[Anomaly]:
        """Mark an anomaly as validated"""
        return self.update(anomaly_id, validated=True)

    def delete(self, anomaly_id: int) -> bool:
        """Delete an anomaly"""
        with Session(self.engine) as session:
            anomaly = session.get(Anomaly, anomaly_id)
            if anomaly:
                session.delete(anomaly)
                session.commit()
                return True
            return False

    def delete_by_analysis(self, analysis_id: int) -> int:
        """Delete all anomalies for an analysis"""
        with Session(self.engine) as session:
            statement = select(Anomaly).where(Anomaly.analysis_id == analysis_id)
            anomalies = session.exec(statement).all()
            count = len(anomalies)

            for anomaly in anomalies:
                session.delete(anomaly)

            session.commit()
            return count
