from datetime import datetime
from unittest.mock import Mock

import pytest


# Mock dataset and datapoint classes
class MockDataset:
    def __init__(self, id, name):
        self.id = id
        self.name = name


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
        MockDataset(1, "dataset1"),
        MockDataset(2, "dataset2"),
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
    assert result[1]["num_entries"] == 2


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


# Mock Analysis class
class MockAnalysis:
    def __init__(self, id, dataset_id, detection_method, name, description=None):
        self.id = id
        self.dataset_id = dataset_id
        self.detection_method = detection_method
        self.name = name
        self.description = description


# Mock Anomaly class
class MockAnomaly:
    def __init__(self, id, analysis_id, start, end):
        self.id = id
        self.analysis_id = analysis_id
        self.start = start
        self.end = end


@pytest.fixture
def mock_analysis_repo():
    repo = Mock()
    analyses = [
        MockAnalysis(1, 1, "IsolationForest", "Analysis 1", "First analysis"),
        MockAnalysis(2, 1, "LOF", "Analysis 2", "Second analysis"),
        MockAnalysis(3, 2, "DBSCAN", "Analysis 3", None),
    ]
    repo.get_by_dataset.side_effect = lambda dataset_id: [a for a in analyses if a.dataset_id == dataset_id]
    repo.get_by_id.side_effect = lambda id: next((a for a in analyses if a.id == id), None)
    return repo


@pytest.fixture
def mock_anomaly_repo():
    repo = Mock()
    anomalies = [
        MockAnomaly(1, 1, datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 11, 0)),
        MockAnomaly(2, 1, datetime(2024, 1, 1, 15, 0), datetime(2024, 1, 1, 16, 0)),
        MockAnomaly(3, 1, datetime(2024, 1, 1, 20, 0), datetime(2024, 1, 1, 21, 0)),
        MockAnomaly(4, 2, datetime(2024, 1, 2, 10, 0), datetime(2024, 1, 2, 11, 0)),
    ]
    repo.get_by_analysis.side_effect = lambda analysis_id: [a for a in anomalies if a.analysis_id == analysis_id]
    return repo


def test_get_analyses(mock_analysis_repo):
    from time_series.dataset_service.overview_service import get_analyses

    result = get_analyses(1, analysis_repo=mock_analysis_repo)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["detection_method"] == "IsolationForest"
    assert result[0]["name"] == "Analysis 1"
    assert result[0]["description"] == "First analysis"
    assert result[1]["id"] == 2
    assert result[1]["detection_method"] == "LOF"


def test_get_analyses_empty_dataset(mock_analysis_repo):
    from time_series.dataset_service.overview_service import get_analyses

    result = get_analyses(999, analysis_repo=mock_analysis_repo)

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_anomalous_ranges(mock_analysis_repo, mock_anomaly_repo):
    from time_series.dataset_service.overview_service import get_anomalous_ranges

    result = get_anomalous_ranges(1, analysis_repo=mock_analysis_repo, anomaly_repo=mock_anomaly_repo)

    assert isinstance(result, dict)
    assert result["dataset_id"] == 1
    assert "items" in result
    assert len(result["items"]) == 3
    assert result["items"][0]["start"] == "2024-01-01T10:00:00"
    assert result["items"][0]["end"] == "2024-01-01T11:00:00"
    assert result["items"][1]["start"] == "2024-01-01T15:00:00"
    assert result["items"][2]["start"] == "2024-01-01T20:00:00"


def test_get_anomalous_ranges_analysis_not_found(mock_analysis_repo, mock_anomaly_repo):
    from time_series.dataset_service.overview_service import get_anomalous_ranges

    result = get_anomalous_ranges(999, analysis_repo=mock_analysis_repo, anomaly_repo=mock_anomaly_repo)

    assert isinstance(result, dict)
    assert result["dataset_id"] is None
    assert result["items"] == []


def test_get_anomalous_ranges_no_anomalies(mock_analysis_repo, mock_anomaly_repo):
    from time_series.dataset_service.overview_service import get_anomalous_ranges

    result = get_anomalous_ranges(3, analysis_repo=mock_analysis_repo, anomaly_repo=mock_anomaly_repo)

    assert isinstance(result, dict)
    assert result["dataset_id"] == 2
    assert result["items"] == []
