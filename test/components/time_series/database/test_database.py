"""
Tests for database services using pytest and SQLite
Run with: uv run pytest test/components/time_series/database/test_database.py
"""

from datetime import datetime, timedelta

import pytest
from sqlmodel import SQLModel, create_engine
from time_series.database import DatapointService, DatasetService


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sample_dataset(test_engine):
    """Create a sample dataset for testing"""
    dataset = DatasetService.create(
        name=f"Test Dataset {datetime.now().timestamp()}",
        start_date=datetime.now(),
        description="Test dataset",
        engine=test_engine,
    )
    yield dataset


@pytest.fixture
def dataset_with_datapoints(sample_dataset, test_engine):
    """Create a dataset with sample datapoints"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    datapoints = [
        {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
        for i in range(10)
    ]
    DatapointService.bulk_create(datapoints, engine=test_engine)
    yield sample_dataset


class TestDatasetService:
    """Tests for DatasetService"""

    def test_create_dataset(self, test_engine):
        """Test creating a dataset"""
        dataset = DatasetService.create(
            name=f"Test Dataset {datetime.now().timestamp()}",
            start_date=datetime.now(),
            description="This is a test dataset",
            engine=test_engine,
        )

        assert dataset.id is not None
        assert dataset.name is not None
        assert dataset.description == "This is a test dataset"

    def test_get_all_datasets(self, sample_dataset, test_engine):
        """Test retrieving all datasets"""
        datasets = DatasetService.get_all(engine=test_engine)

        assert isinstance(datasets, list)
        assert len(datasets) >= 1
        assert any(ds.id == sample_dataset.id for ds in datasets)

    def test_get_dataset_by_id(self, sample_dataset, test_engine):
        """Test retrieving a dataset by ID"""
        dataset = DatasetService.get_by_id(sample_dataset.id, engine=test_engine)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_get_dataset_by_name(self, sample_dataset, test_engine):
        """Test retrieving a dataset by name"""
        dataset = DatasetService.get_by_name(sample_dataset.name, engine=test_engine)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_update_dataset(self, sample_dataset, test_engine):
        """Test updating a dataset"""
        new_description = f"Updated at {datetime.now()}"
        updated_dataset = DatasetService.update(sample_dataset.id, engine=test_engine, description=new_description)

        assert updated_dataset is not None
        assert updated_dataset.description == new_description

    def test_delete_dataset(self, sample_dataset, test_engine):
        """Test deleting a dataset"""
        dataset_id = sample_dataset.id
        success = DatasetService.delete(dataset_id, engine=test_engine)

        assert success is True
        assert DatasetService.get_by_id(dataset_id, engine=test_engine) is None

    def test_get_nonexistent_dataset(self, test_engine):
        """Test getting a dataset that doesn't exist"""
        dataset = DatasetService.get_by_id(99999, engine=test_engine)
        assert dataset is None


class TestDatapointService:
    """Tests for DatapointService"""

    def test_create_datapoint(self, sample_dataset, test_engine):
        """Test creating a single datapoint"""
        now = datetime.now()
        datapoint = DatapointService.create(dataset_id=sample_dataset.id, time=now, value=25.5, engine=test_engine)

        assert datapoint.dataset_id == sample_dataset.id
        assert datapoint.value == 25.5
        assert datapoint.time == now

    def test_bulk_create_datapoints(self, sample_dataset, test_engine):
        """Test creating multiple datapoints"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        datapoints = [
            {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
            for i in range(10)
        ]

        count = DatapointService.bulk_create(datapoints, engine=test_engine)
        assert count == 10

    def test_get_datapoints_by_dataset(self, dataset_with_datapoints, test_engine):
        """Test retrieving all datapoints for a dataset"""
        datapoints = DatapointService.get_by_dataset(dataset_with_datapoints.id, engine=test_engine)

        assert isinstance(datapoints, list)
        assert len(datapoints) == 10

    def test_get_datapoints_range(self, dataset_with_datapoints, test_engine):
        """Test retrieving datapoints within a time range"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        start_time = base_time + timedelta(minutes=2)
        end_time = base_time + timedelta(minutes=7)

        datapoints = DatapointService.get_range(
            dataset_id=dataset_with_datapoints.id, start_time=start_time, end_time=end_time, engine=test_engine
        )

        assert isinstance(datapoints, list)
        assert len(datapoints) == 6  # Minutes 2, 3, 4, 5, 6, 7
        # Verify all datapoints are in the range
        for dp in datapoints:
            assert start_time <= dp.time <= end_time

    def test_delete_old_datapoints(self, dataset_with_datapoints, test_engine):
        """Test deleting old datapoints"""
        before_count = len(DatapointService.get_by_dataset(dataset_with_datapoints.id, engine=test_engine))

        # Delete datapoints older than 5 minutes from base time
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        cutoff_time = base_time + timedelta(minutes=5)
        deleted_count = DatapointService.delete_before(dataset_with_datapoints.id, cutoff_time, engine=test_engine)

        after_count = len(DatapointService.get_by_dataset(dataset_with_datapoints.id, engine=test_engine))
        assert after_count == before_count - deleted_count
        assert deleted_count == 5  # Should delete datapoints 0-4

    def test_datapoints_ordered_by_time(self, dataset_with_datapoints, test_engine):
        """Test that datapoints are returned in time order"""
        datapoints = DatapointService.get_by_dataset(dataset_with_datapoints.id, engine=test_engine)

        times = [dp.time for dp in datapoints]
        assert times == sorted(times), "Datapoints should be ordered by time"


class TestCascadeDelete:
    """Tests for cascade delete behavior"""

    def test_cascade_delete(self, test_engine):
        """Test that deleting a dataset cascades to datapoints"""
        # Create a dataset
        dataset = DatasetService.create(
            name=f"Cascade Test {datetime.now().timestamp()}",
            start_date=datetime.now(),
            description="Testing cascade delete",
            engine=test_engine,
        )

        # Add some datapoints
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        DatapointService.bulk_create(
            [{"dataset_id": dataset.id, "time": base_time + timedelta(minutes=i), "value": float(i)} for i in range(5)],
            engine=test_engine,
        )

        # Verify datapoints exist
        datapoints_before = DatapointService.get_by_dataset(dataset.id, engine=test_engine)
        assert len(datapoints_before) == 5

        # Delete the dataset
        DatasetService.delete(dataset.id, engine=test_engine)

        # Verify datapoints are also deleted (cascade)
        datapoints_after = DatapointService.get_by_dataset(dataset.id, engine=test_engine)
        assert len(datapoints_after) == 0
