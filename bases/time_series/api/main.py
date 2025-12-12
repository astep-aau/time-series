import logging
from datetime import datetime
from typing import Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.customization import CustomizedPage, UseAdditionalFields, UseParamsFields
from sqlmodel import Session
from starlette.middleware.cors import CORSMiddleware
from time_series.database.engine import ENGINE
from time_series.database.unit_of_work import UnitOfWork
from time_series.dataset_service import OverviewService, UploadService

logger = logging.getLogger("api")

app = FastAPI(
    title="Time Series API",
    description="API for managing time series datasets, forecasting and outlier detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session():
    with Session(ENGINE) as session:
        yield session


def get_overview_service(session: Session = Depends(get_session)) -> OverviewService:
    return OverviewService(UnitOfWork(session))


def get_upload_service(session: Session = Depends(get_session)) -> UploadService:
    return UploadService(UnitOfWork(session))


T = TypeVar("T")
DatapointsPage = CustomizedPage[
    Page[T],
    UseParamsFields(size=Query(100, ge=1, le=10000)),
]

RangesPage = CustomizedPage[
    Page[T], UseParamsFields(size=Query(100, ge=1, le=10000)), UseAdditionalFields(dataset_id=int)
]


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
def health_check():
    return "OK"


@app.get("/datasets")
def get_datasets(
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return {"datasets": service.get_all_datasets()}


@app.post("/datasets")
async def create_dataset_endpoint(
    request: Request,
    name: str = Query(description="Name of the dataset"),
    description: str = Query(None, description="Description of the dataset"),
    session: Session = Depends(get_session),
) -> dict:
    csv_content = await request.body()
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        with UnitOfWork(session) as uow:
            service = UploadService(uow)
            result = service.create_dataset(name=name, description=description, csv_content=csv_text)
            uow.commit()
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/datasets/{dataset_id}")
def get_dataset_endpoint(
    dataset_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return service.get_dataset_by_id(dataset_id)


@app.put("/datasets/{dataset_id}")
async def add_dataset_data(request: Request, dataset_id: int, session: Session = Depends(get_session)) -> dict:
    csv_content = await request.body()
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        with UnitOfWork(session) as uow:
            service = UploadService(uow)
            result = service.add_data_to_dataset(dataset_id=dataset_id, csv_content=csv_text)
            uow.commit()
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/datasets/{dataset_id}")
def delete_dataset_endpoint(dataset_id: int, session: Session = Depends(get_session)) -> dict:
    try:
        with UnitOfWork(session) as uow:
            success = uow.datasets.delete(dataset_id)
            if not success:
                raise ValueError(f"Dataset with id {dataset_id} not found")
            uow.commit()
            return {"message": "Dataset deleted successfully", "dataset_id": dataset_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/datasets/{dataset_id}/records")
async def get_records_endpoint(
    dataset_id: int,
    start: Optional[datetime] = Query(None, description="Start datetime for filtering records"),
    end: Optional[datetime] = Query(None, description="End datetime for filtering records"),
    service: OverviewService = Depends(get_overview_service),
) -> DatapointsPage[dict]:
    records_data = service.get_filtered_dataset_records(dataset_id, start, end)
    return paginate(records_data)


@app.get("/datasets/{dataset_id}/analyses")
async def get_analyses_for_dataset_endpoint(
    dataset_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return {"analyses": service.get_analyses(dataset_id)}


@app.get("/analyses/{analysis_id}")
async def get_anomalous_ranges_endpoint(
    analysis_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> RangesPage[dict]:
    result = service.get_anomalous_ranges(analysis_id)
    items = paginate(result["items"], additional_data=({"dataset_id": result["dataset_id"]}))
    return items


add_pagination(app)
