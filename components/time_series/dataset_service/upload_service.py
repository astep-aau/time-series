import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from time_series.database.repository import DatapointRepository, DatasetRepository


def parse_csv_content(csv_content: str) -> list[dict]:
    datapoints: list[dict] = []

    if not csv_content.strip():
        return datapoints

    csv_file = StringIO(csv_content)
    reader = csv.DictReader(csv_file)

    for row in reader:
        unix_time = int(row["unix_time"])
        value = float(row["values"])
        time = datetime.fromtimestamp(unix_time)

        datapoints.append({"time": time, "value": value})

    return datapoints


def create_dataset(
    name: str,
    start_date: datetime,
    description: Optional[str] = None,
    dataset_repo: Optional[DatasetRepository] = None,
) -> dict:
    dataset_repo = dataset_repo or DatasetRepository()

    existing_dataset = dataset_repo.get_by_name(name)
    if existing_dataset:
        raise ValueError(f"Dataset with name '{name}' already exists")

    dataset = dataset_repo.create(name=name, start_date=start_date, description=description)

    if not dataset or not dataset.id:
        raise ValueError("Failed to create dataset")

    return {"id": dataset.id, "name": dataset.name}


def add_data_to_dataset(
    dataset_id: int,
    csv_content: str,
    dataset_repo: Optional[DatasetRepository] = None,
    datapoint_repo: Optional[DatapointRepository] = None,
) -> dict:
    dataset_repo = dataset_repo or DatasetRepository()
    datapoint_repo = datapoint_repo or DatapointRepository()

    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset with id {dataset_id} not found")

    datapoints_added = 0

    if csv_content.strip():
        try:
            parsed_datapoints = parse_csv_content(csv_content)

            for dp in parsed_datapoints:
                dp["dataset_id"] = dataset_id

            if parsed_datapoints:
                datapoint_repo.bulk_create(parsed_datapoints)
                datapoints_added = len(parsed_datapoints)

        except Exception as e:
            raise ValueError(f"Error parsing CSV: {str(e)}")

    return {"dataset_id": dataset_id, "datapoints_added": datapoints_added}


def create_dataset_with_data(
    name: str,
    start_date: datetime,
    description: Optional[str] = None,
    csv_content: str = "",
    dataset_repo: Optional[DatasetRepository] = None,
    datapoint_repo: Optional[DatapointRepository] = None,
) -> dict:
    dataset_repo = dataset_repo or DatasetRepository()
    datapoint_repo = datapoint_repo or DatapointRepository()
    result = create_dataset(name, start_date, description, dataset_repo)
    dataset_id = result["id"]

    datapoints_created = 0

    if csv_content.strip():
        try:
            add_result = add_data_to_dataset(dataset_id, csv_content, dataset_repo, datapoint_repo)
            datapoints_created = add_result["datapoints_added"]
        except ValueError as e:
            dataset_repo.delete(dataset_id)
            raise e

    return {"id": dataset_id, "name": result["name"], "datapoints_created": datapoints_created}


def delete_dataset(
    dataset_id: int,
    dataset_repo: Optional[DatasetRepository] = None,
) -> bool:
    dataset_repo = dataset_repo or DatasetRepository()

    success = dataset_repo.delete(dataset_id)

    if not success:
        raise ValueError(f"Dataset with id {dataset_id} not found")

    return success
