from datetime import datetime
from typing import Dict, List

from time_series.database.repository import (
    PredictionDatapointRepository,
    PredictionRepository,
    PredictionResultRepository,
)


def add_prediction(name: str, date: datetime, user_data: list, prediction: list) -> None:
    prediction_repo = PredictionRepository()
    datapoint_repo = PredictionDatapointRepository()
    result_repo = PredictionResultRepository()
    dataset = prediction_repo.create(name=name, date=date)
    if dataset.id is None:
        return
    if len(user_data) == 2:
        user_data = user_data[0]
    if len(prediction) == 2:
        prediction = prediction[0]
    for dp in user_data:
        datapoint_repo.create(dataset_id=int(dataset.id), time=datetime.now(), value=dp)
    for dp in prediction:
        result_repo.create(dataset_id=int(dataset.id), time=datetime.now(), value=dp)


def get_all_datasets(dataset_repo=None, datapoint_repo=None) -> List[Dict]:
    prediction_repo = PredictionRepository()
    datapoint_repo = PredictionDatapointRepository()
    result_repo = PredictionResultRepository()

    datasets = prediction_repo.get_all()
    result = []

    for dataset in datasets:
        if dataset.id is None:
            result.append({"error": "invalid dataset id"})
            return result
        datapoints = datapoint_repo.get_by_dataset(int(dataset.id))
        results = result_repo.get_by_dataset(int(dataset.id))
        dataset_info = {
            "id": dataset.id,
            "name": dataset.name,
            "user_data": datapoints,
            "prediction": results,
            "date": dataset.date.isoformat() if dataset.date else None,
        }
        result.append(dataset_info)
    return result
