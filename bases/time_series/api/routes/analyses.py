from fastapi import APIRouter, Depends
from fastapi_pagination import paginate
from time_series.api.helpers import get_overview_service
from time_series.api.pagination import RangesPage
from time_series.dataset_service import OverviewService

router = APIRouter()


@router.get("/{analysis_id}")
async def get_anomalous_ranges_endpoint(
    analysis_id: int,
    service: OverviewService = Depends(get_overview_service),
) -> RangesPage[dict]:
    result = service.get_anomalous_ranges(analysis_id)
    items = paginate(result["items"], additional_data=({"dataset_id": result["dataset_id"]}))
    return items
