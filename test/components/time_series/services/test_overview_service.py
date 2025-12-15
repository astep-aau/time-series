from datetime import datetime
from unittest.mock import Mock

import pytest


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


class MockAnalysis:
    def __init__(self, id, dataset_id, detection_method, name, description=None):
        self.id = id
        self.dataset_id = dataset_id
        self.detection_method = detection_method
        self.name = name
        self.description = description


class MockAnomaly:
    def __init__(self, id, analysis_id, start, end):
        self.id = id
        self.analysis_id = analysis_id
        self.start = start
        self.end = end


@pytest.fixture
def mock_uow():
    uow = Mock()

    datasets = [
        MockDataset(1, "dataset1"),
        MockDataset(2, "dataset2"),
    ]
    uow.datasets = Mock()
    uow.datasets.get_all.return_value = datasets
    uow.analyses.get_by_dataset.return_value = []
    uow.datasets.get_by_id.side_effect = lambda id: next((d for d in datasets if d.id == id), None)

    def get_by_dataset(dataset_id):
        if dataset_id == 1:
            return [
                MockDatapoint(datetime(2024, 1, 1, 10, 0)),
                MockDatapoint(datetime(2024, 1, 1, 11, 0)),
                MockDatapoint(datetime(2024, 1, 1, 12, 0)),
            ]
        else:
            return [MockDatapoint(datetime(2024, 2, 1, 10, 0)), MockDatapoint(datetime(2024, 2, 1, 11, 0))]

    uow.datapoints = Mock()
    uow.datapoints.get_by_dataset.side_effect = get_by_dataset

    return uow


@pytest.fixture
def mock_uow_with_values():
    uow = Mock()

    datapoints = [MockDatapointWithValue(i, datetime(2024, 1, 1, i, 0), float(i * 10)) for i in range(1, 11)]

    uow.datapoints = Mock()
    uow.datapoints.get_by_dataset.return_value = datapoints
    uow.datapoints.get_range.return_value = datapoints[2:7]  # Returns datapoints 3-7

    return uow


@pytest.fixture
def mock_uow_with_analyses():
    uow = Mock()

    analyses = [
        MockAnalysis(1, 1, "IsolationForest", "Analysis 1", "First analysis"),
        MockAnalysis(2, 1, "LOF", "Analysis 2", "Second analysis"),
        MockAnalysis(3, 2, "DBSCAN", "Analysis 3", None),
    ]

    anomalies = [
        MockAnomaly(1, 1, datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 11, 0)),
        MockAnomaly(2, 1, datetime(2024, 1, 1, 15, 0), datetime(2024, 1, 1, 16, 0)),
        MockAnomaly(3, 1, datetime(2024, 1, 1, 20, 0), datetime(2024, 1, 1, 21, 0)),
        MockAnomaly(4, 2, datetime(2024, 1, 2, 10, 0), datetime(2024, 1, 2, 11, 0)),
    ]

    uow.analyses = Mock()
    uow.analyses.get_by_dataset.side_effect = lambda dataset_id: [a for a in analyses if a.dataset_id == dataset_id]
    uow.analyses.get_by_id.side_effect = lambda id: next((a for a in analyses if a.id == id), None)

    uow.anomalies = Mock()
    uow.anomalies.get_by_analysis.side_effect = lambda analysis_id: [
        a for a in anomalies if a.analysis_id == analysis_id
    ]

    return uow


def test_get_all_datasets(mock_uow):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow)
    result = service.get_all_datasets()

    assert len(result) == 2
    assert result[0]["num_entries"] == 3
    assert result[1]["num_entries"] == 2


def test_get_dataset_by_id(mock_uow):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow)
    result = service.get_dataset_by_id(1)

    assert result["id"] == 1
    assert result["num_entries"] == 3
    assert result["start_datetime"] == "2024-01-01T10:00:00"
    assert result["end_datetime"] == "2024-01-01T12:00:00"


def test_get_dataset_by_id_not_found(mock_uow):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow)
    result = service.get_dataset_by_id(999)

    assert "error" in result
    assert result["error"] == "Dataset not found"


def test_get_dataset_records_basic(mock_uow_with_values):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_values)
    result = service.get_filtered_dataset_records(1)

    assert isinstance(result, list)
    assert len(result) == 10
    assert result[0]["value"] == 10.0
    assert "time" in result[0]


def test_get_dataset_records_with_date_range(mock_uow_with_values):
    from time_series.services.overview_service import OverviewService

    start = datetime(2024, 1, 1, 3, 0)
    end = datetime(2024, 1, 1, 7, 0)

    service = OverviewService(mock_uow_with_values)
    result = service.get_filtered_dataset_records(1, start=start, end=end)

    assert isinstance(result, list)
    assert len(result) == 5


def test_get_analyses(mock_uow_with_analyses):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_analyses)
    result = service.get_analyses(1)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["detection_method"] == "IsolationForest"
    assert result[0]["name"] == "Analysis 1"
    assert result[0]["description"] == "First analysis"
    assert result[1]["id"] == 2
    assert result[1]["detection_method"] == "LOF"


def test_get_analyses_empty_dataset(mock_uow_with_analyses):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_analyses)
    result = service.get_analyses(999)

    assert isinstance(result, list)
    assert len(result) == 0


def test_get_anomalous_ranges(mock_uow_with_analyses):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_analyses)
    result = service.get_anomalous_ranges(1)

    assert isinstance(result, dict)
    assert result["dataset_id"] == 1
    assert "items" in result
    assert len(result["items"]) == 3
    assert result["items"][0]["start"] == "2024-01-01T10:00:00"
    assert result["items"][0]["end"] == "2024-01-01T11:00:00"
    assert result["items"][1]["start"] == "2024-01-01T15:00:00"
    assert result["items"][2]["start"] == "2024-01-01T20:00:00"


def test_get_anomalous_ranges_analysis_not_found(mock_uow_with_analyses):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_analyses)
    result = service.get_anomalous_ranges(999)

    assert isinstance(result, dict)
    assert result["dataset_id"] is None
    assert result["items"] == []


def test_get_anomalous_ranges_no_anomalies(mock_uow_with_analyses):
    from time_series.services.overview_service import OverviewService

    service = OverviewService(mock_uow_with_analyses)
    result = service.get_anomalous_ranges(3)

    assert isinstance(result, dict)
    assert result["dataset_id"] == 2
    assert result["items"] == []
