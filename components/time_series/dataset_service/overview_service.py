from datetime import datetime
from typing import Dict, List, Optional

from time_series.database.repository import (
    AnalysisRepository,
    AnomalyRepository,
    DatapointRepository,
    DatasetRepository,
)


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


def get_analyses(dataset_id: int, analysis_repo=None) -> List[Dict]:
    analysis_repo = analysis_repo or AnalysisRepository()
    analyses = analysis_repo.get_by_dataset(dataset_id)

    return [
        {
            "id": analysis.id,
            "detection_method": analysis.detection_method,
            "name": analysis.name,
            "description": analysis.description,
        }
        for analysis in analyses
    ]


def get_anomalous_ranges(analysis_id: int, analysis_repo=None, anomaly_repo=None) -> Dict:
    analysis_repo = analysis_repo or AnalysisRepository()
    anomaly_repo = anomaly_repo or AnomalyRepository()

    analysis = analysis_repo.get_by_id(analysis_id)
    if not analysis:
        return {"dataset_id": None, "items": []}

    anomalies = anomaly_repo.get_by_analysis(analysis_id)

    return {
        "dataset_id": analysis.dataset_id,
        "items": [
            {
                "start": anomaly.start.isoformat(),
                "end": anomaly.end.isoformat(),
            }
            for anomaly in anomalies
        ],
    }
