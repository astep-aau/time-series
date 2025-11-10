import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from fastapi_pagination import Page, add_pagination, paginate
from time_series.dataset_service import get_all_datasets, get_dataset_by_id, get_filtered_dataset_records
from time_series.greeting import hello_world

logger = logging.getLogger("rest-api")
app = FastAPI()


@app.get("/")
def root() -> dict:
    logger.info("fastapi root endpoint was called")
    return {"message": hello_world()}


@app.get("/datasets")
def get_datasets() -> dict:
    return {"datasets": get_all_datasets()}


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int) -> dict:
    return get_dataset_by_id(dataset_id)


@app.get("/datasets/{dataset_id}/records", response_model=Page[dict])
def get_records(
    dataset_id: int,
    start: Optional[datetime] = Query(None, description="Start datetime for filtering records"),
    end: Optional[datetime] = Query(None, description="End datetime for filtering records"),
):
    records_data = get_filtered_dataset_records(dataset_id, start, end)
    return paginate(records_data)


add_pagination(app)
