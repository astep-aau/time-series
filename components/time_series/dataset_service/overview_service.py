from datetime import datetime
from typing import Dict, List, Optional

from time_series.database.repository import DatapointRepository, DatasetRepository


def get_all_datasets(dataset_repo=None, datapoint_repo=None) -> List[Dict]:
    dataset_repo = dataset_repo or DatasetRepository()
    datapoint_repo = datapoint_repo or DatapointRepository()

    datasets = dataset_repo.get_all()
    result = []

    for dataset in datasets:
        datapoints = datapoint_repo.get_by_dataset(dataset.id)
        dataset_info = {
            "id": dataset.id,
            "name": dataset.name,
            "num_entries": len(datapoints),
        }
        result.append(dataset_info)
    return result


def get_dataset_by_id(dataset_id: int, dataset_repo=None, datapoint_repo=None) -> Dict:
    dataset_repo = dataset_repo or DatasetRepository()
    datapoint_repo = datapoint_repo or DatapointRepository()

    dataset = dataset_repo.get_by_id(dataset_id)
    if not dataset:
        return {"error": "Dataset not found"}

    datapoints = datapoint_repo.get_by_dataset(dataset_id)
    metadata = {
        "id": dataset.id,
        "name": dataset.name,
        "num_entries": len(datapoints),
        "num_columns": 2,
        "columns": ["time", "value"],
    }

    if datapoints:
        times = [dp.time for dp in datapoints]
        metadata["start_datetime"] = min(times).isoformat()
        metadata["end_datetime"] = max(times).isoformat()
    else:
        metadata["start_datetime"] = None
        metadata["end_datetime"] = None

    return metadata


def get_filtered_dataset_records(
    dataset_id: int,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    datapoint_repo=None,
) -> List[Dict]:
    datapoint_repo = datapoint_repo or DatapointRepository()

    if start is not None and end is not None:
        records = datapoint_repo.get_range(dataset_id, start, end)
    elif start is not None:
        all_records = datapoint_repo.get_by_dataset(dataset_id)
        records = [r for r in all_records if r.time >= start]
    elif end is not None:
        all_records = datapoint_repo.get_by_dataset(dataset_id)
        records = [r for r in all_records if r.time <= end]
    else:
        records = datapoint_repo.get_by_dataset(dataset_id)

    return [
        {
            "time": r.time.isoformat(),
            "value": r.value,
        }
        for r in records
    ]
