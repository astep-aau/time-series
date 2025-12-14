from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi_pagination import paginate
from sqlmodel import Session
from time_series.api.helpers import get_overview_service, get_session
from time_series.api.pagination import DatapointsPage
from time_series.database.unit_of_work import UnitOfWork
from time_series.services import OverviewService, UploadService

router = APIRouter()


@router.get("/")
def get_datasets(
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return {"datasets": service.get_all_datasets()}


@router.post("/")
async def create_dataset_endpoint(
    name: str = Query(description="Name of the dataset"),
    description: str = Query(None, description="Description of the dataset"),
    session: Session = Depends(get_session),
    csv_content: bytes = Body(
        description="CSV content of the dataset",
        example="time,value\n2023-01-01T00:00:00Z,100\n2023-01-01T01:00:00Z,110\n",
    ),
) -> dict:
    csv_text = csv_content.decode("utf-8") if csv_content else ""

    try:
        with UnitOfWork(session) as uow:
            service = UploadService(uow)
            result = service.create_dataset(name=name, description=description, csv_content=csv_text)
            uow.commit()
            return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{dataset_id}")
def get_dataset_endpoint(
    dataset_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return service.get_dataset_by_id(dataset_id)


@router.put("/{dataset_id}")
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


@router.delete("/{dataset_id}")
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


@router.get("/{dataset_id}/records")
async def get_records_endpoint(
    dataset_id: int,
    start: Optional[datetime] = Query(None, description="Start datetime for filtering records"),
    end: Optional[datetime] = Query(None, description="End datetime for filtering records"),
    service: OverviewService = Depends(get_overview_service),
) -> DatapointsPage[dict]:
    records_data = service.get_filtered_dataset_records(dataset_id, start, end)
    return paginate(records_data)


@router.get("/{dataset_id}/analyses")
async def get_analyses_for_dataset_endpoint(
    dataset_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> dict:
    return {"analyses": service.get_analyses(dataset_id)}
