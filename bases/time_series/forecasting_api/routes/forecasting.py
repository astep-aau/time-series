from typing import Any

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, paginate
from time_series.forecasting.data_service import forecastingService
from time_series.forecasting.prediction import predict
from time_series.forecasting_api.helpers import get_forecasting_service

router = APIRouter()


@router.get("/{dataset_id}", response_model=Page[dict[str, Any]] | dict[str, Any])
def get_all_predictions(
    dataset_id: int,
    service: forecastingService = Depends(get_forecasting_service),
):
    result = service.get_all_predictions(dataset_id)

    # If it's an error/details object, return it as-is
    if isinstance(result, dict):
        return result

    # Otherwise it's a list -> paginate it
    return paginate(result)


@router.post("/{dataset_id}")
def add_prediction(
    dataset_id: int,
    model_name: str,
    user_data: list,
    city: str,
    service: forecastingService = Depends(get_forecasting_service),
) -> int:
    predictions = predict(user_data, city=city)
    return service.add_prediction(model_name=model_name, dataset_id=dataset_id, prediction=predictions)
