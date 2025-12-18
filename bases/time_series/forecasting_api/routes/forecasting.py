from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
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
    if isinstance(result, dict):
        return result
    return paginate(result)


@router.post("/{dataset_id}", status_code=201)
def add_prediction(
    dataset_id: int,
    model_name: Annotated[str, Query(min_length=1, description="Name of the model used")],
    city: Annotated[str, Query(min_length=2, description="City name")],
    user_data: Annotated[list[float], Body(..., description="Chronological readings (floats)")],
    service: forecastingService = Depends(get_forecasting_service),
) -> int:
    if len(user_data) < 48:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "USER_DATA_TOO_SHORT",
                "message": f"user_data has {len(user_data)} values, expected at least 48.",
                "fix": "Send at least 48 chronological readings (oldest -> newest).",
            },
        )

    try:
        predictions = predict(user_data, city=city)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_INPUT",
                "message": str(e),
                "fix": "Check city is valid and user_data is floats in chronological order.",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"code": "PREDICTION_FAILED", "message": "Prediction failed unexpectedly."},
        )

    return service.add_prediction(model_name=model_name, dataset_id=dataset_id, prediction=predictions)
