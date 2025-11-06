from datetime import datetime
from unittest.mock import Mock

import pytest


class MockDataset:
    def __init__(self, id, name, start_date):
        self.id = id
        self.name = name
        self.start_date = start_date


@pytest.fixture
def mock_dataset_repo():
    repo = Mock()
    mock_dataset = MockDataset(id=1, name="Test", start_date=datetime.now())
    repo.create.return_value = mock_dataset
    repo.get_by_id.return_value = mock_dataset
    return repo


@pytest.fixture
def mock_datapoint_repo():
    repo = Mock()
    return repo


def test_parse_csv_content():
    from time_series.dataset_service.upload_service import parse_csv_content

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386
1761122533,-0.72571851"""

    datapoints = parse_csv_content(csv_content)

    assert len(datapoints) == 3
    assert datapoints[0]["value"] == -0.69516194
    assert datapoints[1]["value"] == -0.68570386
    assert datapoints[2]["value"] == -0.72571851
    assert isinstance(datapoints[0]["time"], datetime)


def test_parse_empty_csv():
    from time_series.dataset_service.upload_service import parse_csv_content

    datapoints = parse_csv_content("")
    assert len(datapoints) == 0

    datapoints = parse_csv_content("   ")
    assert len(datapoints) == 0


def test_create_empty_dataset(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import create_dataset_with_data

    result = create_dataset_with_data(
        name="Test Dataset",
        start_date=datetime.now(),
        csv_content="",
        dataset_repo=mock_dataset_repo,
        datapoint_repo=mock_datapoint_repo,
    )

    assert result["name"] == "Test"
    assert result["datapoints_created"] == 0
    assert "id" in result


def test_create_dataset_with_csv(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import create_dataset_with_data

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386"""

    result = create_dataset_with_data(
        name="Test Dataset with Data",
        start_date=datetime(2025, 11, 6, 10, 0, 0),
        csv_content=csv_content,
        dataset_repo=mock_dataset_repo,
        datapoint_repo=mock_datapoint_repo,
    )

    assert result["name"] == "Test"
    assert result["datapoints_created"] == 2
    assert "id" in result

    mock_datapoint_repo.bulk_create.assert_called_once()
    call_args = mock_datapoint_repo.bulk_create.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0]["dataset_id"] == 1
    assert call_args[0]["value"] == -0.69516194


def test_create_dataset_with_custom_start_date(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import create_dataset_with_data

    custom_date = datetime(2025, 1, 1, 12, 0, 0)

    result = create_dataset_with_data(
        name="Custom Date Dataset",
        start_date=custom_date,
        csv_content="",
        dataset_repo=mock_dataset_repo,
        datapoint_repo=mock_datapoint_repo,
    )

    mock_dataset_repo.create.assert_called_once_with(
        name="Custom Date Dataset", start_date=custom_date, description=None
    )
    assert "id" in result


def test_create_dataset(mock_dataset_repo):
    from time_series.dataset_service.upload_service import create_dataset

    result = create_dataset(
        name="Test Dataset", start_date=datetime(2025, 11, 6, 10, 0, 0), dataset_repo=mock_dataset_repo
    )

    assert result["name"] == "Test"
    assert result["id"] == 1
    mock_dataset_repo.create.assert_called_once_with(
        name="Test Dataset", start_date=datetime(2025, 11, 6, 10, 0, 0), description=None
    )


def test_add_data_to_dataset(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import add_data_to_dataset

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386"""

    result = add_data_to_dataset(
        dataset_id=1, csv_content=csv_content, dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo
    )

    assert result["dataset_id"] == 1
    assert result["datapoints_added"] == 2

    mock_datapoint_repo.bulk_create.assert_called_once()
    call_args = mock_datapoint_repo.bulk_create.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0]["dataset_id"] == 1


def test_add_data_to_nonexistent_dataset(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import add_data_to_dataset

    mock_dataset_repo.get_by_id.return_value = None

    csv_content = """unix_time,values
1761122529,-0.69516194"""

    with pytest.raises(ValueError, match="Dataset with id 999 not found"):
        add_data_to_dataset(
            dataset_id=999, csv_content=csv_content, dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo
        )


def test_add_empty_data_to_dataset(mock_dataset_repo, mock_datapoint_repo):
    from time_series.dataset_service.upload_service import add_data_to_dataset

    result = add_data_to_dataset(
        dataset_id=1, csv_content="", dataset_repo=mock_dataset_repo, datapoint_repo=mock_datapoint_repo
    )

    assert result["dataset_id"] == 1
    assert result["datapoints_added"] == 0
    mock_datapoint_repo.bulk_create.assert_not_called()
