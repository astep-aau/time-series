from datetime import datetime, timedelta, timezone
from typing import List

from time_series.database.repository import (
    AnalysisRepository,
    PredictionRepository,
)


def add_prediction(model_name: str, dataset_id: int, user_data: list, prediction: list):
    """
    Create an analysis entry and store prediction values linked to it.
    """

    analysis_repo = AnalysisRepository()
    prediction_repo = PredictionRepository()

    # 1. Create analysis record with timezone-aware datetime
    now_utc = datetime.now(timezone.utc)

    analysis = analysis_repo.create(
        dataset_id=dataset_id,
        model=model_name,
        name=f"{model_name}-{now_utc.isoformat()}",
        description="Generated forecast",
    )

    # 2. Save prediction results with UTC timestamps
    #    If you want each prediction to have a unique timestamp:
    base_time = now_utc

    for i, value in enumerate(prediction):
        prediction_repo.create(
            analysis_id=analysis.id,
            time=base_time + timedelta(seconds=i),  # unique timestamp per prediction
            value=float(value),
        )

    return analysis.id


def get_all_predictions(dataset_id: int) -> List[dict]:
    """
    Return all analyses + predictions for a dataset.
    """

    analysis_repo = AnalysisRepository()
    prediction_repo = PredictionRepository()

    analyses = analysis_repo.get_by_dataset(dataset_id)
    results = []

    for analysis in analyses:
        preds = prediction_repo.get_by_analysis(analysis.id)

        results.append(
            {
                "analysis_id": analysis.id,
                "model": analysis.model,
                "name": analysis.name,
                "predictions": preds,
            }
        )

    return results
