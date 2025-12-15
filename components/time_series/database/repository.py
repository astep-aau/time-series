from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, col, select


from .engine import engine as default_engine
from .models import (
    Analysis,
    Anomaly,
    AnomalyType,
    Datapoint,
    Dataset,
    PredictionDatapoint,
    PredictionDataset,
    PredictionResult,
)



class DatasetRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, description: Optional[str] = None) -> Dataset:
        dataset = Dataset(name=name, description=description)
        self.session.add(dataset)
        self.session.flush()
        self.session.refresh(dataset)
        return dataset

    def get_all(self) -> List[Dataset]:
        return list(self.session.exec(select(Dataset)).all())

    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        return self.session.get(Dataset, dataset_id)

    def get_by_name(self, name: str) -> Optional[Dataset]:
        statement = select(Dataset).where(Dataset.name == name)
        return self.session.exec(statement).first()

    def update(self, dataset_id: int, **kwargs) -> Optional[Dataset]:
        dataset = self.session.get(Dataset, dataset_id)
        if dataset:
            for key, value in kwargs.items():
                setattr(dataset, key, value)
            self.session.add(dataset)
            self.session.flush()
            self.session.refresh(dataset)
        return dataset

    def delete(self, dataset_id: int) -> bool:
        dataset = self.session.get(Dataset, dataset_id)
        if dataset:
            self.session.delete(dataset)
            self.session.flush()
            return True
        return False


class DatapointRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, dataset_id: int, time: datetime, value: float) -> Datapoint:
        datapoint = Datapoint(dataset_id=dataset_id, time=time, value=float(value))
        self.session.add(datapoint)
        self.session.flush()
        self.session.refresh(datapoint)
        return datapoint

    def bulk_create(self, datapoints: List[dict]) -> int:
        for dp_data in datapoints:
            datapoint = Datapoint(**dp_data)
            self.session.add(datapoint)
        self.session.flush()
        return len(datapoints)

    def get_by_dataset(self, dataset_id: int) -> List[Datapoint]:
        statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id).order_by(col(Datapoint.time))
        return list(self.session.exec(statement).all())

    def get_range(self, dataset_id: int, start_time: datetime, end_time: datetime) -> List[Datapoint]:
        statement = (
            select(Datapoint)
            .where(Datapoint.dataset_id == dataset_id, Datapoint.time >= start_time, Datapoint.time <= end_time)
            .order_by(col(Datapoint.time))
        )
        return list(self.session.exec(statement).all())

    def delete_before(self, dataset_id: int, cutoff_time: datetime) -> int:
        statement = select(Datapoint).where(Datapoint.dataset_id == dataset_id, Datapoint.time < cutoff_time)
        datapoints = self.session.exec(statement).all()
        count = len(datapoints)

        for dp in datapoints:
            self.session.delete(dp)

        self.session.flush()
        return count


class AnalysisRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        dataset_id: int,
        detection_method: str,
        name: str,
        description: Optional[str] = None,
    ) -> Analysis:
        analysis = Analysis(
            dataset_id=dataset_id,
            detection_method=detection_method,
            name=name,
            description=description,
        )
        self.session.add(analysis)
        self.session.flush()
        self.session.refresh(analysis)
        return analysis

    def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        return self.session.get(Analysis, analysis_id)

    def get_by_dataset(self, dataset_id: int) -> List[Analysis]:
        statement = select(Analysis).where(Analysis.dataset_id == dataset_id).order_by(col(Analysis.id))
        return list(self.session.exec(statement).all())

    def update(self, analysis_id: int, **kwargs) -> Optional[Analysis]:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis:
            for key, value in kwargs.items():
                setattr(analysis, key, value)
            self.session.add(analysis)
            self.session.flush()
            self.session.refresh(analysis)
        return analysis

    def delete(self, analysis_id: int) -> bool:
        analysis = self.session.get(Analysis, analysis_id)
        if analysis:
            self.session.delete(analysis)
            self.session.flush()
            return True
        return False


class AnomalyRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        analysis_id: int,
        start: datetime,
        end: datetime,
        type: AnomalyType,
        validated: bool = False,
    ) -> Anomaly:
        anomaly = Anomaly(
            analysis_id=analysis_id,
            start=start,
            end=end,
            type=type,
            validated=validated,
        )
        self.session.add(anomaly)
        self.session.flush()
        self.session.refresh(anomaly)
        return anomaly

    def bulk_create(self, anomalies: List[dict]) -> int:
        for anomaly_data in anomalies:
            anomaly = Anomaly(**anomaly_data)
            self.session.add(anomaly)
        self.session.flush()
        return len(anomalies)

    def get_by_id(self, anomaly_id: int) -> Optional[Anomaly]:
        return self.session.get(Anomaly, anomaly_id)

    def get_by_analysis(self, analysis_id: int) -> List[Anomaly]:
        statement = select(Anomaly).where(Anomaly.analysis_id == analysis_id).order_by(col(Anomaly.start))
        return list(self.session.exec(statement).all())

    def get_by_type(self, analysis_id: int, anomaly_type: AnomalyType) -> List[Anomaly]:
        statement = (
            select(Anomaly)
            .where(Anomaly.analysis_id == analysis_id, Anomaly.type == anomaly_type)
            .order_by(col(Anomaly.start))
        )
        return list(self.session.exec(statement).all())

    def get_validated(self, analysis_id: int, validated: bool = True) -> List[Anomaly]:
        statement = (
            select(Anomaly)
            .where(Anomaly.analysis_id == analysis_id, Anomaly.validated == validated)
            .order_by(col(Anomaly.start))
        )
        return list(self.session.exec(statement).all())

    def get_range(self, analysis_id: int, start_time: datetime, end_time: datetime) -> List[Anomaly]:
        statement = (
            select(Anomaly)
            .where(
                Anomaly.analysis_id == analysis_id,
                Anomaly.start <= end_time,
                Anomaly.end >= start_time,
            )
            .order_by(col(Anomaly.start))
        )
        return list(self.session.exec(statement).all())

    def update(self, anomaly_id: int, **kwargs) -> Optional[Anomaly]:
        anomaly = self.session.get(Anomaly, anomaly_id)
        if anomaly:
            for key, value in kwargs.items():
                setattr(anomaly, key, value)
            self.session.add(anomaly)
            self.session.flush()
            self.session.refresh(anomaly)
        return anomaly

    def validate(self, anomaly_id: int) -> Optional[Anomaly]:
        return self.update(anomaly_id, validated=True)

    def delete(self, anomaly_id: int) -> bool:
        anomaly = self.session.get(Anomaly, anomaly_id)
        if anomaly:
            self.session.delete(anomaly)
            self.session.flush()
            return True
        return False

    def delete_by_analysis(self, analysis_id: int) -> int:
        statement = select(Anomaly).where(Anomaly.analysis_id == analysis_id)
        anomalies = self.session.exec(statement).all()
        count = len(anomalies)

        for anomaly in anomalies:
            self.session.delete(anomaly)


            session.commit()
            return count


class PredictionRepository:
    """Repository for prediction operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(self, name: str, date: datetime) -> PredictionDataset:
        with Session(self.engine) as session:
            dataset = PredictionDataset(name=name, date=date)
            session.add(dataset)
            session.commit()
            session.refresh(dataset)
            return dataset

    def get_all(self) -> List[PredictionDataset]:
        with Session(self.engine) as session:
            return list(session.exec(select(PredictionDataset)).all())

    def get_by_id(self, dataset_id: int) -> Optional[PredictionDataset]:
        with Session(self.engine) as session:
            return session.get(PredictionDataset, dataset_id)

    def get_by_name(self, name: str) -> Optional[PredictionDataset]:
        with Session(self.engine) as session:
            statement = select(PredictionDataset).where(PredictionDataset.name == name)
            return session.exec(statement).first()

    def update(self, dataset_id: int, **kwargs) -> Optional[PredictionDataset]:
        with Session(self.engine) as session:
            dataset = session.get(PredictionDataset, dataset_id)
            if dataset:
                for key, value in kwargs.items():
                    setattr(dataset, key, value)
                session.add(dataset)
                session.commit()
                session.refresh(dataset)
            return dataset

    def delete(self, dataset_id: int) -> bool:
        with Session(self.engine) as session:
            dataset = session.get(PredictionDataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False


class PredictionDatapointRepository:
    """Repository for prediction datapoint operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(self, dataset_id: int, time: datetime, value: float) -> PredictionDatapoint:
        with Session(self.engine) as session:
            datapoint = PredictionDatapoint(dataset_id=dataset_id, time=time, value=float(value))
            session.add(datapoint)
            session.commit()
            session.refresh(datapoint)
            return datapoint

    def get_by_dataset(self, dataset_id: int) -> List[PredictionDatapoint]:
        with Session(self.engine) as session:
            statement = (
                select(PredictionDatapoint)
                .where(PredictionDatapoint.dataset_id == dataset_id)
                .order_by(col(PredictionDatapoint.time))
            )
            return list(session.exec(statement).all())

    def delete(self, dataset_id: int) -> bool:
        with Session(self.engine) as session:
            dataset = session.get(PredictionDataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False


class PredictionResultRepository:
    """Repository for prediction datapoint operations"""

    def __init__(self, engine=None):
        self.engine = engine or default_engine

    def create(self, dataset_id: int, time: datetime, value: float) -> PredictionResult:
        with Session(self.engine) as session:
            datapoint = PredictionResult(dataset_id=dataset_id, time=time, value=float(value))
            session.add(datapoint)
            session.commit()
            session.refresh(datapoint)
            return datapoint

    def get_by_dataset(self, dataset_id: int) -> List[PredictionResult]:
        with Session(self.engine) as session:
            statement = (
                select(PredictionResult)
                .where(PredictionResult.dataset_id == dataset_id)
                .order_by(col(PredictionResult.time))
            )
            return list(session.exec(statement).all())

    def delete(self, dataset_id: int) -> bool:
        with Session(self.engine) as session:
            dataset = session.get(PredictionDataset, dataset_id)
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            return False

