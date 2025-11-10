from datetime import datetime
from unittest.mock import Mock

import pytest


# Mock dataset and datapoint classes
class MockDataset:
    def __init__(self, id, name, start_date=None):
        self.id = id
        self.name = name
        self.start_date = start_date


class MockDatapoint:
    def __init__(self, time):
        self.time = time


class MockDatapointWithValue:
    def __init__(self, id, time, value):
        self.id = id
        self.time = time
        self.value = value


@pytest.fixture
def mock_dataset_repo():
    repo = Mock()
    repo.get_all.return_value = [
        MockDataset(1, "dataset1", datetime(2024, 1, 1)),
        MockDataset(2, "dataset2", datetime(2024, 2, 1)),
    ]
    repo.get_by_id.side_effect = lambda id: next((d for d in repo.get_all.return_value if d.id == id), None)
    return repo


@pytest.fixture
def mock_datapoint_repo():
    repo = Mock()
    repo.get_by_dataset.side_effect = (
        lambda dataset_id: [
            MockDatapoint(datetime(2024, 1, 1, 10, 0)),
            MockDatapoint(datetime(2024, 1, 1, 11, 0)),
            MockDatapoint(datetime(2024, 1, 1, 12, 0)),
        ]
        if dataset_id == 1
        else [MockDatapoint(datetime(2024, 2, 1, 10, 0)), MockDatapoint(datetime(2024, 2, 1, 11, 0))]
    )
    return repo


@pytest.fixture
def mock_datapoint_repo_with_values():
    repo = Mock()
    datapoints = [MockDatapointWithValue(i, datetime(2024, 1, 1, i, 0), float(i * 10)) for i in range(1, 11)]
    repo.get_by_dataset.return_value = datapoints
    repo.get_range.return_value = datapoints[2:7]  # Returns datapoints 3-7
    return repo


# Tests
# Import functions inside tests to avoid loading models during test collection


def test_get_all_datasets(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.overview_service import get_all_datasets

    result = get_all_datasets(dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo)
    assert len(result) == 2
    assert result[0]["num_entries"] == 3
    assert result[0]["start_date"] == "2024-01-01T00:00:00"
    assert result[1]["num_entries"] == 2
    assert result[1]["start_date"] == "2024-02-01T00:00:00"


def test_get_dataset_by_id(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.overview_service import get_dataset_by_id

    result = get_dataset_by_id(1, dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo)
    assert result["id"] == 1
    assert result["num_entries"] == 3
    assert result["start_datetime"] == "2024-01-01T10:00:00"
    assert result["end_datetime"] == "2024-01-01T12:00:00"


def test_get_dataset_by_id_not_found(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.overview_service import get_dataset_by_id

    result = get_dataset_by_id(999, dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo)
    assert "error" in result
    assert result["error"] == "Dataset not found"


def test_get_dataset_records_basic(mock_datapoint_repo_with_values):
    from time_series.dataset_service.overview_service import get_filtered_dataset_records

    result = get_filtered_dataset_records(1, datapoint_repo=mock_datapoint_repo_with_values)

    assert isinstance(result, list)
    assert len(result) == 10
    assert result[0]["value"] == 10.0
    assert "time" in result[0]


def test_get_dataset_records_with_date_range(mock_datapoint_repo_with_values):
    from time_series.dataset_service.overview_service import get_filtered_dataset_records

    start = datetime(2024, 1, 1, 3, 0)
    end = datetime(2024, 1, 1, 7, 0)

    result = get_filtered_dataset_records(1, start=start, end=end, datapoint_repo=mock_datapoint_repo_with_values)

    assert isinstance(result, list)
    assert len(result) == 5
