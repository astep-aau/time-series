from datetime import datetime, timedelta

import pytest
from sqlmodel import SQLModel, create_engine
from time_series.database import DatapointRepository, DatasetRepository


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def dataset_repo(test_engine):
    """Create a DatasetRepository instance"""
    return DatasetRepository(engine=test_engine)


@pytest.fixture
def datapoint_repo(test_engine):
    """Create a DatapointRepository instance"""
    return DatapointRepository(engine=test_engine)


@pytest.fixture
def sample_dataset(dataset_repo):
    """Create a sample dataset for testing"""
    dataset = dataset_repo.create(
        name=f"Test Dataset {datetime.now().timestamp()}",
        start_date=datetime.now(),
        description="Test dataset",
    )
    yield dataset


@pytest.fixture
def dataset_with_datapoints(sample_dataset, datapoint_repo):
    """Create a dataset with sample datapoints"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    datapoints = [
        {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
        for i in range(10)
    ]
    datapoint_repo.bulk_create(datapoints)
    yield sample_dataset


class TestDatasetRepositry:
    """Tests for DatasetRepository"""

    def test_create_dataset(self, dataset_repo):
        """Test creating a dataset"""
        dataset = dataset_repo.create(
            name=f"Test Dataset {datetime.now().timestamp()}",
            start_date=datetime.now(),
            description="This is a test dataset",
        )

        assert dataset.id is not None
        assert dataset.name is not None
        assert dataset.description == "This is a test dataset"

    def test_get_all_datasets(self, sample_dataset, dataset_repo):
        """Test retrieving all datasets"""
        datasets = dataset_repo.get_all()

        assert isinstance(datasets, list)
        assert len(datasets) >= 1
        assert any(ds.id == sample_dataset.id for ds in datasets)

    def test_get_dataset_by_id(self, sample_dataset, dataset_repo):
        """Test retrieving a dataset by ID"""
        dataset = dataset_repo.get_by_id(sample_dataset.id)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_get_dataset_by_name(self, sample_dataset, dataset_repo):
        """Test retrieving a dataset by name"""
        dataset = dataset_repo.get_by_name(sample_dataset.name)

        assert dataset is not None
        assert dataset.id == sample_dataset.id
        assert dataset.name == sample_dataset.name

    def test_update_dataset(self, sample_dataset, dataset_repo):
        """Test updating a dataset"""
        new_description = f"Updated at {datetime.now()}"
        updated_dataset = dataset_repo.update(sample_dataset.id, description=new_description)

        assert updated_dataset is not None
        assert updated_dataset.description == new_description

    def test_delete_dataset(self, sample_dataset, dataset_repo):
        """Test deleting a dataset"""
        dataset_id = sample_dataset.id
        success = dataset_repo.delete(dataset_id)

        assert success is True
        assert dataset_repo.get_by_id(dataset_id) is None

    def test_get_nonexistent_dataset(self, dataset_repo):
        """Test getting a dataset that doesn't exist"""
        dataset = dataset_repo.get_by_id(99999)
        assert dataset is None


class TestDatapointRepository:
    """Tests for DatapointRepository"""

    def test_create_datapoint(self, sample_dataset, datapoint_repo):
        """Test creating a single datapoint"""
        now = datetime.now()
        datapoint = datapoint_repo.create(dataset_id=sample_dataset.id, time=now, value=25.5)

        assert datapoint.dataset_id == sample_dataset.id
        assert datapoint.value == 25.5
        assert datapoint.time == now

    def test_bulk_create_datapoints(self, sample_dataset, datapoint_repo):
        """Test creating multiple datapoints"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        datapoints = [
            {"dataset_id": sample_dataset.id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
            for i in range(10)
        ]

        count = datapoint_repo.bulk_create(datapoints)
        assert count == 10

    def test_get_datapoints_by_dataset(self, dataset_with_datapoints, datapoint_repo):
        """Test retrieving all datapoints for a dataset"""
        datapoints = datapoint_repo.get_by_dataset(dataset_with_datapoints.id)

        assert isinstance(datapoints, list)
        assert len(datapoints) == 10

    def test_get_datapoints_range(self, dataset_with_datapoints, datapoint_repo):
        """Test retrieving datapoints within a time range"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        start_time = base_time + timedelta(minutes=2)
        end_time = base_time + timedelta(minutes=7)

        datapoints = datapoint_repo.get_range(
            dataset_id=dataset_with_datapoints.id, start_time=start_time, end_time=end_time
        )

        assert isinstance(datapoints, list)
        assert len(datapoints) == 6  # Minutes 2, 3, 4, 5, 6, 7
        # Verify all datapoints are in the range
        for dp in datapoints:
            assert start_time <= dp.time <= end_time

    def test_delete_old_datapoints(self, dataset_with_datapoints, datapoint_repo):
        """Test deleting old datapoints"""
        before_count = len(datapoint_repo.get_by_dataset(dataset_with_datapoints.id))

        # Delete datapoints older than 5 minutes from base time
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        cutoff_time = base_time + timedelta(minutes=5)
        deleted_count = datapoint_repo.delete_before(dataset_with_datapoints.id, cutoff_time)

        after_count = len(datapoint_repo.get_by_dataset(dataset_with_datapoints.id))
        assert after_count == before_count - deleted_count
        assert deleted_count == 5  # Should delete datapoints 0-4

    def test_datapoints_ordered_by_time(self, dataset_with_datapoints, datapoint_repo):
        """Test that datapoints are returned in time order"""
        datapoints = datapoint_repo.get_by_dataset(dataset_with_datapoints.id)

        times = [dp.time for dp in datapoints]
        assert times == sorted(times), "Datapoints should be ordered by time"


class TestCascadeDelete:
    """Tests for cascade delete behavior"""

    def test_cascade_delete(self, dataset_repo, datapoint_repo):
        """Test that deleting a dataset cascades to datapoints"""
        # Create a dataset
        dataset = dataset_repo.create(
            name=f"Cascade Test {datetime.now().timestamp()}",
            start_date=datetime.now(),
            description="Testing cascade delete",
        )

        # Add some datapoints
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        datapoint_repo.bulk_create(
            [{"dataset_id": dataset.id, "time": base_time + timedelta(minutes=i), "value": float(i)} for i in range(5)]
        )

        # Verify datapoints exist
        datapoints_before = datapoint_repo.get_by_dataset(dataset.id)
        assert len(datapoints_before) == 5

        # Delete the dataset
        dataset_repo.delete(dataset.id)

        # Verify datapoints are also deleted (cascade)
        datapoints_after = datapoint_repo.get_by_dataset(dataset.id)
        assert len(datapoints_after) == 0
