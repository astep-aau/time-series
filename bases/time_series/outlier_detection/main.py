import logging
from datetime import datetime
from typing import Optional, TypeVar

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields, UseParamsFields
from starlette.middleware.cors import CORSMiddleware
from time_series.dataset_service import (
    add_data_to_dataset,
    create_dataset,
    delete_dataset,
    get_all_datasets,
    get_analyses,
    get_anomalous_ranges,
    get_dataset_by_id,
    get_filtered_dataset_records,
)
from time_series.greeting import hello_world

logger = logging.getLogger("rest-api")
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

T = TypeVar("T")
DatapointsPage = CustomizedPage[
    Page[T],
    UseParamsFields(size=Query(100, ge=1, le=10000)),
]

RangesPage = CustomizedPage[
    Page[T], UseParamsFields(size=Query(100, ge=1, le=10000)), UseAdditionalFields(dataset_id=int)
]


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
    description: str = Query(None, description="Description of the dataset"),
) -> dict:
    csv_content = await request.body()
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        result = create_dataset(name=name, description=description, csv_content=csv_text)
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


@app.get("/datasets/{dataset_id}/records")
async def get_records(
    dataset_id: int,
    start: Optional[datetime] = Query(None, description="Start datetime for filtering records"),
    end: Optional[datetime] = Query(None, description="End datetime for filtering records"),
) -> DatapointsPage[dict]:
    records_data = get_filtered_dataset_records(dataset_id, start, end)
    return paginate(records_data)


@app.get("/datasets/{dataset_id}/analyses")
async def get_analyses_for_dataset(dataset_id: int) -> dict:
    return {"analyses": get_analyses(dataset_id)}


@app.get("/analyses/{analysis_id}")
async def get_anomalous_ranges_endpoint(analysis_id: int) -> RangesPage[dict]:
    result = get_anomalous_ranges(analysis_id)
    items = paginate(result["items"], additional_data=({"dataset_id": result["dataset_id"]}))
    return items


add_pagination(app)
