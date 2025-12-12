from sqlmodel import Session

from .repository import AnalysisRepository, AnomalyRepository, DatapointRepository, DatasetRepository


class UnitOfWork:
    def __init__(self, session: Session):
        self._session: Session = session
        self.datasets: DatasetRepository = DatasetRepository(self._session)
        self.datapoints: DatapointRepository = DatapointRepository(self._session)
        self.analyses: AnalysisRepository = AnalysisRepository(self._session)
        self.anomalies: AnomalyRepository = AnomalyRepository(self._session)

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self.rollback()

    def commit(self):
        self._session.commit()

    def rollback(self):
        self._session.rollback()

    def flush(self):
        self._session.flush()
