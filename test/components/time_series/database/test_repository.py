from datetime import datetime, timedelta

import pytest
from sqlmodel import SQLModel, create_engine
from time_series.database import (
    AnomalyRepository,
    AnomalyType,
    DatapointRepository,
    DatasetRepository,
)


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


@pytest.fixture
def anomaly_repo(test_engine):
    """Create an AnomalyRepository instance"""
    return AnomalyRepository(engine=test_engine)


@pytest.fixture
def dataset_with_simple_anomalies(sample_dataset, anomaly_repo):
    """Create a dataset with 3 simple point anomalies"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    anomalies = [
        {
            "dataset_id": sample_dataset.id,
            "start": base_time + timedelta(hours=i),
            "end": base_time + timedelta(hours=i, minutes=30),
            "type": AnomalyType.point,
            "validated": False,
        }
        for i in range(3)
    ]
    anomaly_repo.bulk_create(anomalies)
    yield sample_dataset


@pytest.fixture
def dataset_with_mixed_types(sample_dataset, anomaly_repo):
    """Create a dataset with both point and contextual anomalies"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    anomalies = [
        {
            "dataset_id": sample_dataset.id,
            "start": base_time + timedelta(hours=i),
            "end": base_time + timedelta(hours=i, minutes=30),
            "type": AnomalyType.point if i % 2 == 0 else AnomalyType.contextual,
            "validated": False,
        }
        for i in range(6)
    ]
    anomaly_repo.bulk_create(anomalies)
    yield sample_dataset


@pytest.fixture
def dataset_with_validated_anomalies(sample_dataset, anomaly_repo):
    """Create a dataset with mix of validated and unvalidated anomalies"""
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    anomalies = [
        {
            "dataset_id": sample_dataset.id,
            "start": base_time + timedelta(hours=i),
            "end": base_time + timedelta(hours=i, minutes=30),
            "type": AnomalyType.point,
            "validated": i < 3,
        }
        for i in range(6)
    ]
    anomaly_repo.bulk_create(anomalies)
    yield sample_dataset


class TestAnomalyRepository:
    """Tests for AnomalyRepository"""

    def test_create_anomaly(self, sample_dataset, anomaly_repo):
        """Test creating a single anomaly"""
        start_time = datetime(2024, 1, 1, 12, 0, 0)
        end_time = datetime(2024, 1, 1, 12, 30, 0)

        anomaly = anomaly_repo.create(
            dataset_id=sample_dataset.id,
            start=start_time,
            end=end_time,
            type=AnomalyType.point,
            validated=False,
        )

        assert anomaly.id is not None
        assert anomaly.dataset_id == sample_dataset.id
        assert anomaly.start == start_time
        assert anomaly.end == end_time
        assert anomaly.type == AnomalyType.point
        assert anomaly.validated is False

    def test_bulk_create_anomalies(self, sample_dataset, anomaly_repo):
        """Test creating multiple anomalies"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        anomalies = [
            {
                "dataset_id": sample_dataset.id,
                "start": base_time + timedelta(hours=i),
                "end": base_time + timedelta(hours=i, minutes=30),
                "type": AnomalyType.point,
                "validated": False,
            }
            for i in range(5)
        ]

        count = anomaly_repo.bulk_create(anomalies)
        assert count == 5

    def test_get_anomaly_by_id(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test retrieving an anomaly by ID"""
        anomalies = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)
        first_anomaly = anomalies[0]

        retrieved = anomaly_repo.get_by_id(first_anomaly.id)

        assert retrieved is not None
        assert retrieved.id == first_anomaly.id
        assert retrieved.dataset_id == dataset_with_simple_anomalies.id

    def test_get_anomalies_by_dataset(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test retrieving all anomalies for a dataset"""
        anomalies = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)

        assert isinstance(anomalies, list)
        assert len(anomalies) == 3

    def test_get_anomalies_by_type(self, dataset_with_mixed_types, anomaly_repo):
        """Test retrieving anomalies by type"""
        point_anomalies = anomaly_repo.get_by_type(dataset_with_mixed_types.id, AnomalyType.point)
        contextual_anomalies = anomaly_repo.get_by_type(dataset_with_mixed_types.id, AnomalyType.contextual)

        assert len(point_anomalies) == 3  # Indices 0, 2, 4
        assert len(contextual_anomalies) == 3  # Indices 1, 3, 5

        for anomaly in point_anomalies:
            assert anomaly.type == AnomalyType.point

        for anomaly in contextual_anomalies:
            assert anomaly.type == AnomalyType.contextual

    def test_get_validated_anomalies(self, dataset_with_validated_anomalies, anomaly_repo):
        """Test retrieving validated vs unvalidated anomalies"""
        validated = anomaly_repo.get_validated(dataset_with_validated_anomalies.id, validated=True)
        unvalidated = anomaly_repo.get_validated(dataset_with_validated_anomalies.id, validated=False)

        assert len(validated) == 3  # Indices 0, 1, 2
        assert len(unvalidated) == 3  # Indices 3, 4, 5

        for anomaly in validated:
            assert anomaly.validated is True

        for anomaly in unvalidated:
            assert anomaly.validated is False

    def test_get_anomalies_in_range(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test retrieving anomalies within a time range"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        start_time = base_time + timedelta(hours=0, minutes=15)
        end_time = base_time + timedelta(hours=1, minutes=45)

        anomalies = anomaly_repo.get_range(
            dataset_id=dataset_with_simple_anomalies.id, start_time=start_time, end_time=end_time
        )

        # Should include anomalies that overlap with the range
        # Anomaly 0: 0:00-0:30 (overlaps)
        # Anomaly 1: 1:00-1:30 (overlaps)
        assert len(anomalies) == 2

    def test_update_anomaly(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test updating an anomaly"""
        anomalies = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)
        first_anomaly = anomalies[0]

        new_end_time = first_anomaly.end + timedelta(hours=1)
        updated = anomaly_repo.update(first_anomaly.id, end=new_end_time, type=AnomalyType.contextual)

        assert updated is not None
        assert updated.end == new_end_time
        assert updated.type == AnomalyType.contextual

    def test_validate_anomaly(self, sample_dataset, anomaly_repo):
        """Test marking an anomaly as validated"""
        anomaly = anomaly_repo.create(
            dataset_id=sample_dataset.id,
            start=datetime(2024, 1, 1, 12, 0, 0),
            end=datetime(2024, 1, 1, 12, 30, 0),
            type=AnomalyType.point,
            validated=False,
        )

        assert anomaly.validated is False

        validated_anomaly = anomaly_repo.validate(anomaly.id)

        assert validated_anomaly is not None
        assert validated_anomaly.validated is True

    def test_delete_anomaly(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test deleting an anomaly"""
        anomalies = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)
        first_anomaly = anomalies[0]
        anomaly_id = first_anomaly.id

        success = anomaly_repo.delete(anomaly_id)

        assert success is True
        assert anomaly_repo.get_by_id(anomaly_id) is None

        # Verify count decreased
        remaining = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)
        assert len(remaining) == 2

    def test_delete_by_dataset(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test deleting all anomalies for a dataset"""
        count = anomaly_repo.delete_by_dataset(dataset_with_simple_anomalies.id)

        assert count == 3

        remaining = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)
        assert len(remaining) == 0

    def test_get_nonexistent_anomaly(self, anomaly_repo):
        """Test getting an anomaly that doesn't exist"""
        anomaly = anomaly_repo.get_by_id(99999)
        assert anomaly is None

    def test_anomalies_ordered_by_start_time(self, dataset_with_simple_anomalies, anomaly_repo):
        """Test that anomalies are returned in start time order"""
        anomalies = anomaly_repo.get_by_dataset(dataset_with_simple_anomalies.id)

        start_times = [anomaly.start for anomaly in anomalies]
        assert start_times == sorted(start_times), "Anomalies should be ordered by start time"


class TestAnomalyCascadeDelete:
    """Tests for cascade delete behavior with anomalies"""

    def test_cascade_delete_dataset_removes_anomalies(self, dataset_repo, anomaly_repo):
        """Test that deleting a dataset cascades to anomalies"""
        # Create a dataset
        dataset = dataset_repo.create(
            name=f"Cascade Test {datetime.now().timestamp()}",
            start_date=datetime.now(),
            description="Testing cascade delete with anomalies",
        )

        # Add some anomalies
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        anomaly_repo.bulk_create(
            [
                {
                    "dataset_id": dataset.id,
                    "start": base_time + timedelta(hours=i),
                    "end": base_time + timedelta(hours=i, minutes=30),
                    "type": AnomalyType.point,
                    "validated": False,
                }
                for i in range(5)
            ]
        )

        # Verify anomalies exist
        anomalies_before = anomaly_repo.get_by_dataset(dataset.id)
        assert len(anomalies_before) == 5

        # Delete the dataset
        dataset_repo.delete(dataset.id)

        # Verify anomalies are also deleted (cascade)
        anomalies_after = anomaly_repo.get_by_dataset(dataset.id)
        assert len(anomalies_after) == 0


class TestAnomalyEdgeCases:
    """Tests for edge cases"""

    def test_create_anomaly_with_same_start_end(self, sample_dataset, anomaly_repo):
        """Test creating an anomaly where start and end are the same (point in time)"""
        time_point = datetime(2024, 1, 1, 12, 0, 0)

        anomaly = anomaly_repo.create(
            dataset_id=sample_dataset.id,
            start=time_point,
            end=time_point,
            type=AnomalyType.point,
        )

        assert anomaly.start == anomaly.end

    def test_overlapping_anomalies(self, sample_dataset, anomaly_repo):
        """Test creating overlapping anomalies (should be allowed)"""
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        anomaly1 = anomaly_repo.create(
            dataset_id=sample_dataset.id,
            start=base_time,
            end=base_time + timedelta(hours=2),
            type=AnomalyType.contextual,
        )

        anomaly2 = anomaly_repo.create(
            dataset_id=sample_dataset.id,
            start=base_time + timedelta(hours=1),
            end=base_time + timedelta(hours=3),
            type=AnomalyType.point,
        )

        assert anomaly1.id != anomaly2.id
        anomalies = anomaly_repo.get_by_dataset(sample_dataset.id)
        assert len(anomalies) == 2

    def test_multiple_datasets_anomaly_isolation(self, dataset_repo, anomaly_repo):
        """Test that anomalies are properly isolated between datasets"""
        dataset1 = dataset_repo.create(name=f"Dataset 1 {datetime.now().timestamp()}", start_date=datetime.now())
        dataset2 = dataset_repo.create(name=f"Dataset 2 {datetime.now().timestamp()}", start_date=datetime.now())

        base_time = datetime(2024, 1, 1, 12, 0, 0)

        # Add anomalies to dataset1
        anomaly_repo.bulk_create(
            [
                {
                    "dataset_id": dataset1.id,
                    "start": base_time + timedelta(hours=i),
                    "end": base_time + timedelta(hours=i, minutes=30),
                    "type": AnomalyType.point,
                    "validated": False,
                }
                for i in range(3)
            ]
        )

        # Add anomalies to dataset2
        anomaly_repo.bulk_create(
            [
                {
                    "dataset_id": dataset2.id,
                    "start": base_time + timedelta(hours=i),
                    "end": base_time + timedelta(hours=i, minutes=30),
                    "type": AnomalyType.contextual,
                    "validated": True,
                }
                for i in range(5)
            ]
        )

        anomalies1 = anomaly_repo.get_by_dataset(dataset1.id)
        anomalies2 = anomaly_repo.get_by_dataset(dataset2.id)

        assert len(anomalies1) == 3
        assert len(anomalies2) == 5
