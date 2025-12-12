from sqlmodel import Session

from .repository import (
    AnalysisRepository,
    AnomalyRepository,
    DatapointRepository,
    DatasetRepository,
    PredictionRepository,
)


class UnitOfWork:
    def __init__(self, session: Session):
        self._session: Session = session
        self.datasets: DatasetRepository = DatasetRepository(session=self._session)
        self.datapoints: DatapointRepository = DatapointRepository(session=self._session)
        self.analyses: AnalysisRepository = AnalysisRepository(session=self._session)
        self.anomalies: AnomalyRepository = AnomalyRepository(session=self._session)
        self.predictions: PredictionRepository = PredictionRepository(session=self._session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def flush(self):
        self._session.flush()
