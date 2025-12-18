from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlmodel import Session
from time_series.database import UnitOfWork
from time_series.outlier_detection import AnalysisConfig
from time_series.outlier_detection.run import run_lstmae_analysis
from time_series.outlier_detection_api.helpers import get_session

router = APIRouter()


@router.post("/{dataset_id}/lstmae")
def create_lstmae_analysis(
    dataset_id: int,
    config: AnalysisConfig,
    background_tasks: BackgroundTasks,
    name: str,
    description: Optional[str] = None,
    session: Session = Depends(get_session),
):
    with UnitOfWork(session=session) as uow:
        analysis = uow.analyses.create(
            dataset_id=dataset_id,
            detection_method="lstmae",
            name=name,
            description=description,
        )
        uow.commit()

    background_tasks.add_task(run_lstmae_analysis, dataset_id=dataset_id, analysis_id=analysis.id, config=config)  # type: ignore

    return analysis.id
