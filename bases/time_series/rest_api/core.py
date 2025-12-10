import logging
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from time_series.dataset_service import (
    add_data_to_dataset,
    create_dataset,
    delete_dataset,
    get_all_datasets,
    get_dataset_by_id,
)
from time_series.forecast import add_prediction, get_all_predictions, predict
from time_series.greeting import hello_world
from time_series.rest_api.requestModels import PredictionCreateRequest

logger = logging.getLogger("rest-api")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    logger.info("fastapi root endpoint was called")
    return {"message": hello_world()}


@app.get("/datasets")
def get_datasets() -> dict:
    return {"datasets": get_all_datasets()}


@app.post("/datasets")
async def create_dataset_endpoint(
    request: Request,
    name: str = Query(description="Name of the dataset"),
    start_date: str = Query(description="Start date in ISO format."),
    description: str = Query(None, description="Description of the dataset"),
) -> dict:
    try:
        parsed_start_date = datetime.fromisoformat(start_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid start_date format: {start_date}. Expected ISO format.",
        )

    csv_content = await request.body()
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        result = create_dataset(name=name, start_date=parsed_start_date, description=description, csv_content=csv_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int) -> dict:
    return get_dataset_by_id(dataset_id)


@app.put("/datasets/{dataset_id}")
async def add_dataset_data(request: Request, dataset_id: int) -> dict:
    csv_content = await request.body()
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        result = add_data_to_dataset(dataset_id=dataset_id, csv_content=csv_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/datasets/{dataset_id}")
def delete_dataset_endpoint(dataset_id: int) -> dict:
    try:
        delete_dataset(dataset_id)
        return {"message": "Dataset deleted successfully", "dataset_id": dataset_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# forecasting endpoint
# TODO implement the endpoints for analysis and forecasting
@app.get("/analysis/predictions/{dataset_id}")
def get_analysis(dataset_id: int) -> List[dict]:
    try:
        return get_all_predictions(dataset_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("analysis/predictions")
def create_prediction(req: PredictionCreateRequest):
    try:
        # 1. Run your ML model to get forecast list
        prediction_list = predict(user_data=req.user_data, city=req.city)

        # 2. Store it as an analysis + prediction rows
        analysis_id = add_prediction(
            model_name=req.model_name, dataset_id=req.dataset_id, user_data=req.user_data, prediction=prediction_list
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"analysis_id": analysis_id, "prediction_count": len(prediction_list)}
