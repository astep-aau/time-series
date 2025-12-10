from datetime import datetime
from typing import Dict, List, Optional

from time_series.database.unit_of_work import UnitOfWork


class OverviewService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all_datasets(self) -> List[Dict]:
        datasets = self.uow.datasets.get_all()
        result = []
        for dataset in datasets:
            if dataset.id is None:
                continue
            datapoints = self.uow.datapoints.get_by_dataset(dataset.id)
            dataset_info = {
                "id": dataset.id,
                "name": dataset.name,
                "num_entries": len(datapoints),
            }
            result.append(dataset_info)
        return result

    def get_dataset_by_id(self, dataset_id: int) -> Dict:
        dataset = self.uow.datasets.get_by_id(dataset_id)
        if not dataset:
            return {"error": "Dataset not found"}

        datapoints = self.uow.datapoints.get_by_dataset(dataset_id)
        metadata = {
            "id": dataset.id,
            "name": dataset.name,
            "num_entries": len(datapoints),
            "num_columns": 2,
            "columns": ["time", "value"],
        }

        if datapoints:
            times = [dp.time for dp in datapoints]
            metadata["start_datetime"] = min(times).isoformat()
            metadata["end_datetime"] = max(times).isoformat()
        else:
            metadata["start_datetime"] = None
            metadata["end_datetime"] = None

        return metadata

    def get_filtered_dataset_records(
        self,
        dataset_id: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict]:
        if start is not None and end is not None:
            records = self.uow.datapoints.get_range(dataset_id, start, end)
        elif start is not None:
            all_records = self.uow.datapoints.get_by_dataset(dataset_id)
            records = [r for r in all_records if r.time >= start]
        elif end is not None:
            all_records = self.uow.datapoints.get_by_dataset(dataset_id)
            records = [r for r in all_records if r.time <= end]
        else:
            records = self.uow.datapoints.get_by_dataset(dataset_id)

        return [
            {
                "time": r.time.isoformat(),
                "value": r.value,
            }
            for r in records
        ]

    def get_analyses(self, dataset_id: int) -> List[Dict]:
        analyses = self.uow.analyses.get_by_dataset(dataset_id)
        return [
            {
                "id": analysis.id,
                "detection_method": analysis.detection_method,
                "name": analysis.name,
                "description": analysis.description,
            }
            for analysis in analyses
        ]

    def get_anomalous_ranges(self, analysis_id: int) -> Dict:
        analysis = self.uow.analyses.get_by_id(analysis_id)
        if not analysis:
            return {"dataset_id": None, "items": []}

        anomalies = self.uow.anomalies.get_by_analysis(analysis_id)
        return {
            "dataset_id": analysis.dataset_id,
            "items": [
                {
                    "start": anomaly.start.isoformat(),
                    "end": anomaly.end.isoformat(),
                }
                for anomaly in anomalies
            ],
        }
