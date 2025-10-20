"""
Tests for database services
Run with: uv run development/test_database.py
"""

from datetime import datetime, timedelta

from sqlmodel import SQLModel

from components.time_series.database.engine import engine
from components.time_series.database.service import DatapointService, DatasetService


def setup_test_db():
    """Create all tables for testing"""
    SQLModel.metadata.create_all(engine)
    print("✓ Database tables created")


def test_create_dataset():
    """Test creating a dataset"""
    print("\n=== Test: Create Dataset ===")

    dataset = DatasetService.create(
        name=f"Test Dataset {datetime.now().timestamp()}",
        start_date=datetime.now(),
        description="This is a test dataset",
    )

    assert dataset.id is not None, "Dataset should have an ID"
    assert dataset.name is not None, "Dataset should have a name"
    print(f"✓ Created dataset: {dataset.name} (ID: {dataset.id})")
    return dataset


def test_get_all_datasets():
    """Test retrieving all datasets"""
    print("\n=== Test: Get All Datasets ===")

    datasets = DatasetService.get_all()

    assert isinstance(datasets, list), "Should return a list"
    print(f"✓ Found {len(datasets)} dataset(s)")

    for ds in datasets:
        print(f"  - {ds.name} (ID: {ds.id})")

    return datasets


def test_get_dataset_by_id(dataset_id: int):
    """Test retrieving a dataset by ID"""
    print("\n=== Test: Get Dataset by ID ===")

    dataset = DatasetService.get_by_id(dataset_id)

    assert dataset is not None, f"Dataset with ID {dataset_id} should exist"
    assert dataset.id == dataset_id, "Dataset ID should match"
    print(f"✓ Retrieved dataset: {dataset.name}")
    return dataset


def test_get_dataset_by_name(name: str):
    """Test retrieving a dataset by name"""
    print("\n=== Test: Get Dataset by Name ===")

    dataset = DatasetService.get_by_name(name)

    assert dataset is not None, f"Dataset with name '{name}' should exist"
    assert dataset.name == name, "Dataset name should match"
    print(f"✓ Retrieved dataset: {dataset.name} (ID: {dataset.id})")
    return dataset


def test_update_dataset(dataset_id: int):
    """Test updating a dataset"""
    print("\n=== Test: Update Dataset ===")

    new_description = f"Updated at {datetime.now()}"
    updated_dataset = DatasetService.update(dataset_id, description=new_description)

    assert updated_dataset is not None, "Update should return the dataset"
    assert updated_dataset.description == new_description, "Description should be updated"
    print(f"✓ Updated dataset {dataset_id}")
    print(f"  New description: {updated_dataset.description}")
    return updated_dataset


def test_create_datapoint(dataset_id: int):
    """Test creating a single datapoint"""
    print("\n=== Test: Create Datapoint ===")

    datapoint = DatapointService.create(dataset_id=dataset_id, time=datetime.now(), value=25.5)

    assert datapoint.dataset_id == dataset_id, "Datapoint should belong to dataset"
    assert datapoint.value == 25.5, "Datapoint value should match"
    print(f"✓ Created datapoint: {datapoint.time} = {datapoint.value}")
    return datapoint


def test_bulk_create_datapoints(dataset_id: int):
    """Test creating multiple datapoints"""
    print("\n=== Test: Bulk Create Datapoints ===")

    base_time = datetime.now()
    datapoints = [
        {"dataset_id": dataset_id, "time": base_time + timedelta(minutes=i), "value": 20.0 + (i * 0.5)}
        for i in range(10)
    ]

    count = DatapointService.bulk_create(datapoints)

    assert count == 10, "Should create 10 datapoints"
    print(f"✓ Created {count} datapoints")
    return count


def test_get_datapoints_by_dataset(dataset_id: int):
    """Test retrieving all datapoints for a dataset"""
    print("\n=== Test: Get Datapoints by Dataset ===")

    datapoints = DatapointService.get_by_dataset(dataset_id)

    assert isinstance(datapoints, list), "Should return a list"
    print(f"✓ Found {len(datapoints)} datapoint(s)")

    for dp in datapoints[:5]:  # Show first 5
        print(f"  - {dp.time}: {dp.value}")

    if len(datapoints) > 5:
        print(f"  ... and {len(datapoints) - 5} more")

    return datapoints


def test_get_datapoints_range(dataset_id: int):
    """Test retrieving datapoints within a time range"""
    print("\n=== Test: Get Datapoints by Time Range ===")

    now = datetime.now()
    start_time = now - timedelta(minutes=5)
    end_time = now + timedelta(minutes=5)

    datapoints = DatapointService.get_range(dataset_id=dataset_id, start_time=start_time, end_time=end_time)

    assert isinstance(datapoints, list), "Should return a list"
    print(f"✓ Found {len(datapoints)} datapoint(s) in range")
    print(f"  Range: {start_time} to {end_time}")

    for dp in datapoints[:3]:
        print(f"  - {dp.time}: {dp.value}")

    return datapoints


def test_delete_old_datapoints(dataset_id: int):
    """Test deleting old datapoints"""
    print("\n=== Test: Delete Old Datapoints ===")

    # Get count before deletion
    before_count = len(DatapointService.get_by_dataset(dataset_id))

    # Delete datapoints older than 3 minutes ago
    cutoff_time = datetime.now() - timedelta(minutes=3)
    deleted_count = DatapointService.delete_before(dataset_id, cutoff_time)

    # Get count after deletion
    after_count = len(DatapointService.get_by_dataset(dataset_id))

    print(f"✓ Deleted {deleted_count} datapoint(s)")
    print(f"  Before: {before_count}, After: {after_count}")

    assert after_count == before_count - deleted_count, "Count should match deletion"
    return deleted_count


def test_delete_dataset(dataset_id: int):
    """Test deleting a dataset"""
    print("\n=== Test: Delete Dataset ===")

    success = DatasetService.delete(dataset_id)

    assert success is True, "Deletion should succeed"

    # Verify it's deleted
    deleted_dataset = DatasetService.get_by_id(dataset_id)
    assert deleted_dataset is None, "Dataset should no longer exist"

    print(f"✓ Deleted dataset {dataset_id}")
    return success


def test_cascade_delete():
    """Test that deleting a dataset cascades to datapoints"""
    print("\n=== Test: Cascade Delete ===")

    # Create a dataset
    dataset = DatasetService.create(
        name=f"Cascade Test {datetime.now().timestamp()}",
        start_date=datetime.now(),
        description="Testing cascade delete",
    )

    # Add some datapoints
    DatapointService.bulk_create(
        [{"dataset_id": dataset.id, "time": datetime.now() + timedelta(minutes=i), "value": float(i)} for i in range(5)]
    )

    # Verify datapoints exist
    datapoints_before = DatapointService.get_by_dataset(dataset.id)
    assert len(datapoints_before) == 5, "Should have 5 datapoints"

    # Delete the dataset
    DatasetService.delete(dataset.id)

    # Verify datapoints are also deleted (cascade)
    datapoints_after = DatapointService.get_by_dataset(dataset.id)
    assert len(datapoints_after) == 0, "Datapoints should be cascade deleted"

    print(f"✓ Cascade delete working: {len(datapoints_before)} datapoints deleted with dataset")


def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "=" * 50)
    print("RUNNING DATABASE SERVICE TESTS")
    print("=" * 50)

    try:
        # Setup
        setup_test_db()

        # Test dataset operations
        dataset = test_create_dataset()
        test_get_all_datasets()
        test_get_dataset_by_id(dataset.id)
        test_get_dataset_by_name(dataset.name)
        test_update_dataset(dataset.id)

        # Test datapoint operations
        test_create_datapoint(dataset.id)
        test_bulk_create_datapoints(dataset.id)
        test_get_datapoints_by_dataset(dataset.id)
        test_get_datapoints_range(dataset.id)
        test_delete_old_datapoints(dataset.id)

        # Test cascade delete
        test_cascade_delete()

        # Cleanup - delete the test dataset
        test_delete_dataset(dataset.id)

        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
