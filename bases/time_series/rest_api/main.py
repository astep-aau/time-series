import logging

from fastapi import FastAPI
from time_series.dataset_service import get_all_datasets, get_dataset_by_id
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
def get_dataset(dataset_id: str) -> dict:
    return get_dataset_by_id(dataset_id)
