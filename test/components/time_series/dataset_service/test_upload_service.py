from datetime import datetime
from unittest.mock import Mock

import pytest


class MockDataset:
    def __init__(self, id, name):
        self.id = id
        self.name = name


@pytest.fixture
def mock_uow():
    uow = Mock()

    mock_dataset = MockDataset(id=1, name="Test")

    uow.datasets = Mock()
    uow.datasets.create.return_value = mock_dataset
    uow.datasets.get_by_id.return_value = mock_dataset
    uow.datasets.get_by_name.return_value = None
    uow.datasets.delete.return_value = True

    uow.datapoints = Mock()
    uow.datapoints.bulk_create.return_value = 0

    uow.commit = Mock()
    uow.rollback = Mock()

    return uow


def test_parse_csv_content():
    from time_series.dataset_service.upload_service import UploadService

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386
1761122533,-0.72571851"""

    datapoints = UploadService.parse_csv_content(csv_content)

    assert len(datapoints) == 3
    assert datapoints[0]["value"] == -0.69516194
    assert datapoints[1]["value"] == -0.68570386
    assert datapoints[2]["value"] == -0.72571851
    assert isinstance(datapoints[0]["time"], datetime)


def test_parse_empty_csv():
    from time_series.dataset_service.upload_service import UploadService

    datapoints = UploadService.parse_csv_content("")
    assert len(datapoints) == 0

    datapoints = UploadService.parse_csv_content("   ")
    assert len(datapoints) == 0


def test_create_empty_dataset(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    service = UploadService(mock_uow)
    result = service.create_dataset(
        name="Test Dataset",
        csv_content="",
    )

    assert result["name"] == "Test"
    assert result["datapoints_created"] == 0
    assert "id" in result


def test_create_dataset_with_csv(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386"""

    service = UploadService(mock_uow)
    result = service.create_dataset(
        name="Test Dataset with Data",
        csv_content=csv_content,
    )

    assert result["name"] == "Test"
    assert result["datapoints_created"] == 2
    assert "id" in result

    mock_uow.datapoints.bulk_create.assert_called_once()
    call_args = mock_uow.datapoints.bulk_create.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0]["dataset_id"] == 1
    assert call_args[0]["value"] == -0.69516194


def test_create_dataset(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    service = UploadService(mock_uow)
    result = service.create_dataset(name="Test Dataset")

    assert result["name"] == "Test"
    assert result["id"] == 1
    mock_uow.datasets.create.assert_called_once_with(name="Test Dataset", description=None)


def test_add_data_to_dataset(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    csv_content = """unix_time,values
1761122529,-0.69516194
1761122531,-0.68570386"""

    service = UploadService(mock_uow)
    result = service.add_data_to_dataset(dataset_id=1, csv_content=csv_content)

    assert result["dataset_id"] == 1
    assert result["datapoints_added"] == 2

    mock_uow.datapoints.bulk_create.assert_called_once()
    call_args = mock_uow.datapoints.bulk_create.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0]["dataset_id"] == 1


def test_add_data_to_nonexistent_dataset(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    mock_uow.datasets.get_by_id.return_value = None

    csv_content = """unix_time,values
1761122529,-0.69516194"""

    service = UploadService(mock_uow)
    with pytest.raises(ValueError, match="Dataset with id 999 not found"):
        service.add_data_to_dataset(dataset_id=999, csv_content=csv_content)


def test_add_empty_data_to_dataset(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    service = UploadService(mock_uow)
    result = service.add_data_to_dataset(dataset_id=1, csv_content="")

    assert result["dataset_id"] == 1
    assert result["datapoints_added"] == 0
    mock_uow.datapoints.bulk_create.assert_not_called()


def test_create_dataset_with_duplicate_name(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    existing_dataset = MockDataset(id=1, name="Existing Dataset")
    mock_uow.datasets.get_by_name.return_value = existing_dataset

    service = UploadService(mock_uow)
    with pytest.raises(ValueError, match="Dataset with name 'Existing Dataset' already exists"):
        service.create_dataset(name="Existing Dataset")

    mock_uow.datasets.create.assert_not_called()


def test_create_dataset_without_name(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    service = UploadService(mock_uow)
    with pytest.raises(TypeError):
        service.create_dataset()
    mock_uow.datasets.create.assert_not_called()


def test_create_dataset_with_invalid_csv(mock_uow):
    from time_series.dataset_service.upload_service import UploadService

    invalid_csv_content = """x, y
1761122529,-0.69516194"""

    service = UploadService(mock_uow)
    with pytest.raises(ValueError, match="CSV must contain 'unix_time' and 'values' columns"):
        service.create_dataset(
            name="Invalid CSV Dataset",
            csv_content=invalid_csv_content,
        )
    mock_uow.datasets.create.assert_not_called()
    mock_uow.datapoints.bulk_create.assert_not_called()
