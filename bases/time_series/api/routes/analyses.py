from fastapi import APIRouter, Depends, Query
from fastapi_pagination import paginate
from sqlmodel import Session
from time_series.api.helpers import get_overview_service, get_session
from time_series.api.pagination import RangesPage
from time_series.database import UnitOfWork
from time_series.services import OverviewService

router = APIRouter()


@router.get("/{analysis_id}")
async def get_anomalous_ranges_endpoint(
    analysis_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> RangesPage[dict]:
    result = service.get_anomalous_ranges(analysis_id)
    items = paginate(result["items"], additional_data=({"dataset_id": result["dataset_id"]}))
    return items


@router.post("/{dataset_id}/analyses")
async def create_analysis_endpoint(
    dataset_id: int,
    session: Session = Depends(get_session),
    name: str = Query(description="Name of the analysis"),
    description: str = Query(None, description="Description of the analysis"),
    detection_method: str = Query(description="Description of the analysis"),
) -> dict:
    with UnitOfWork(session) as uow:
        analysis = uow.analyses.create(
            dataset_id=dataset_id, name=name, description=description, detection_method=detection_method
        )
        uow.commit()
        return {
            "id": analysis.id,
            "dataset_id": analysis.dataset_id,
            "name": analysis.name,
            "description": analysis.description,
            "detection_method": analysis.detection_method,
        }
