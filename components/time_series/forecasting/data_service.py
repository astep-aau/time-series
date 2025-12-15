from datetime import datetime, timedelta, timezone
from typing import List

from time_series.database.models import Analysis
from time_series.database.unit_of_work import UnitOfWork


class forecastingService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def add_prediction(self, model_name: str, dataset_id: int, prediction: list):
        """
        Create an analysis entry and store prediction values linked to it.
        """

        # 1. Create analysis record with timezone-aware datetime
        now_utc = datetime.now(timezone.utc)

        analysis = self.uow.analyses.create(
            dataset_id=dataset_id,
            detection_method=model_name,
            name=f"{model_name}-{now_utc.isoformat()}",
            description="Generated forecast",
        )

        # 2. Save prediction results with UTC timestamps
        #    If you want each prediction to have a unique timestamp:
        base_time = now_utc

        assert analysis.id is not None
        for i, value in enumerate(prediction):
            self.uow.prediction.create(
                analysis_id=analysis.id,
                time=base_time + timedelta(seconds=i),  # unique timestamp per prediction
                value=float(value),
            )

        return analysis.id

    def get_all_predictions(self, dataset_id: int) -> List[dict] | dict:
        """
        Return all analyses + predictions for a dataset.
        """

        analyses: List[Analysis] = self.uow.analyses.get_by_dataset(dataset_id)

        if not analyses:
            return {"dataset_id": None, "items": []}

        results = []

        for analysis in analyses:
            assert analysis.id is not None
            preds = self.uow.prediction.get_by_analysis(analysis.id)

            results.append(
                {
                    "analysis_id": analysis.id,
                    "detection_method": analysis.detection_method,
                    "name": analysis.name,
                    "predictions": preds,
                }
            )

        return results
