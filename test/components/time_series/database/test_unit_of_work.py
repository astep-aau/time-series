from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine
from time_series.database.models import AnomalyType
from time_series.database.unit_of_work import UnitOfWork


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///file:memdb?mode=memory&cache=shared&uri=true", echo=False)
    with engine.connect() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS timeseries")
        conn.commit()
    SQLModel.metadata.create_all(engine)

    yield engine
    engine.dispose()


def test_unit_of_work_commit_success(test_engine):
    """Test that all operations commit together successfully"""
    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.create(name="test_dataset", description="Test description")
            assert dataset.id is not None

            datapoints = [
                {"dataset_id": dataset.id, "time": datetime(2024, 1, 1, 12, 0), "value": 10.5},
                {"dataset_id": dataset.id, "time": datetime(2024, 1, 2, 12, 0), "value": 20.3},
            ]
            uow.datapoints.bulk_create(datapoints)
            uow.commit()

    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.get_by_name("test_dataset")
            assert dataset is not None
            assert dataset.description == "Test description"

            datapoints = uow.datapoints.get_by_dataset(dataset.id)
            assert len(datapoints) == 2
            assert datapoints[0].value == 10.5
            assert datapoints[1].value == 20.3


def test_unit_of_work_rollback_on_exception(test_engine):
    """Test that all operations rollback together on exception"""
    try:
        with Session(test_engine) as session:
            with UnitOfWork(session=session) as uow:
                dataset = uow.datasets.create(name="test_dataset", description="Test description")
                assert dataset.id is not None

                datapoints = [
                    {"dataset_id": dataset.id, "time": datetime(2024, 1, 1, 12, 0), "value": 10.5},
                ]
                uow.datapoints.bulk_create(datapoints)
                raise ValueError("Something went wrong!")
    except ValueError:
        pass

    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.get_by_name("test_dataset")
            assert dataset is None


def test_unit_of_work_prevents_duplicate_names(test_engine):
    """Test that checking and creating in same transaction prevents race conditions"""
    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            uow.datasets.create(name="duplicate_name")
            uow.commit()

    with pytest.raises(ValueError):
        with Session(test_engine) as session:
            with UnitOfWork(session=session) as uow:
                existing = uow.datasets.get_by_name("duplicate_name")
                if existing:
                    raise ValueError("Dataset already exists")

                uow.datasets.create(name="duplicate_name")
                uow.commit()


def test_unit_of_work_complex_operation(test_engine):
    """Test complex multi-repository operation with atomicity"""
    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.create(name="complex_test")

            datapoints = [
                {"dataset_id": dataset.id, "time": datetime(2024, 1, i, 12, 0), "value": float(i)} for i in range(1, 6)
            ]
            uow.datapoints.bulk_create(datapoints)

            analysis = uow.analyses.create(
                dataset_id=dataset.id,
                detection_method="test_method",
                name="Test Analysis",
            )

            anomalies = [
                {
                    "analysis_id": analysis.id,
                    "start": datetime(2024, 1, 2, 0, 0),
                    "end": datetime(2024, 1, 3, 0, 0),
                    "type": AnomalyType.point,
                    "validated": False,
                }
            ]
            uow.anomalies.bulk_create(anomalies)
            uow.commit()

    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.get_by_name("complex_test")
            assert dataset is not None

            datapoints = uow.datapoints.get_by_dataset(dataset.id)
            assert len(datapoints) == 5

            analyses = uow.analyses.get_by_dataset(dataset.id)
            assert len(analyses) == 1

            anomalies = uow.anomalies.get_by_analysis(analyses[0].id)
            assert len(anomalies) == 1
            assert anomalies[0].type == AnomalyType.point


def test_unit_of_work_partial_failure_rollback(test_engine):
    """Test that partial failure causes complete rollback"""
    try:
        with Session(test_engine) as session:
            with UnitOfWork(session=session) as uow:
                dataset = uow.datasets.create(name="partial_test")

                datapoints = [
                    {"dataset_id": dataset.id, "time": datetime(2024, 1, 1, 12, 0), "value": 10.5},
                    {"dataset_id": dataset.id, "time": datetime(2024, 1, 2, 12, 0), "value": 20.3},
                ]
                uow.datapoints.bulk_create(datapoints)

                uow.analyses.create(
                    dataset_id=dataset.id,
                    detection_method="test",
                    name="Test Analysis",
                )

                raise Exception("Simulated failure during anomaly creation")
    except Exception:
        pass

    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.get_by_name("partial_test")
            assert dataset is None

            all_datasets = uow.datasets.get_all()
            assert len(all_datasets) == 0


def test_unit_of_work_manual_rollback(test_engine):
    """Test manual rollback functionality"""
    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.create(name="manual_rollback_test")
            uow.datapoints.bulk_create(
                [
                    {"dataset_id": dataset.id, "time": datetime(2024, 1, 1, 12, 0), "value": 10.5},
                ]
            )
            uow.rollback()

    with Session(test_engine) as session:
        with UnitOfWork(session=session) as uow:
            dataset = uow.datasets.get_by_name("manual_rollback_test")
            assert dataset is None
