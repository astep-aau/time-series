import logging

from sqlmodel import Session

from .repository import AnalysisRepository, AnomalyRepository, DatapointRepository, DatasetRepository

logger = logging.getLogger(__name__)


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
        logger.info("COMMIT!")
        self._session.commit()

    def rollback(self):
        logger.info("ROLLBACK!")
        self._session.rollback()

    def flush(self):
        logger.info("FLUSH!")
        self._session.flush()
