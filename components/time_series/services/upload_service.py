import csv
from datetime import datetime
from io import StringIO
from typing import Optional

from time_series.database.unit_of_work import UnitOfWork


class UploadService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    @staticmethod
    def parse_csv_content(csv_content: str) -> list[dict]:
        datapoints: list[dict] = []

        if not csv_content.strip():
            return datapoints

        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)

        if not reader.fieldnames or "unix_time" not in reader.fieldnames or "values" not in reader.fieldnames:
            raise ValueError("CSV must contain 'unix_time' and 'values' columns")

        for row in reader:
            unix_time = int(row["unix_time"])
            value = float(row["values"])
            time = datetime.fromtimestamp(unix_time)

            datapoints.append({"time": time, "value": value})

        return datapoints

    def add_data_to_dataset(self, dataset_id: int, csv_content: str) -> dict:
        dataset = self.uow.datasets.get_by_id(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset with id {dataset_id} not found")

        datapoints_added = 0
        if csv_content.strip():
            try:
                parsed_datapoints = self.parse_csv_content(csv_content)
                for dp in parsed_datapoints:
                    dp["dataset_id"] = dataset_id

                if parsed_datapoints:
                    self.uow.datapoints.bulk_create(parsed_datapoints)
                    datapoints_added = len(parsed_datapoints)
            except Exception as e:
                raise ValueError(f"Error parsing CSV: {str(e)}")

        return {"dataset_id": dataset_id, "datapoints_added": datapoints_added}

    def create_dataset(self, name: str, description: Optional[str] = None, csv_content: str = "") -> dict:
        existing_dataset = self.uow.datasets.get_by_name(name)
        if existing_dataset:
            raise ValueError(f"Dataset with name '{name}' already exists")

        if csv_content.strip():
            self.parse_csv_content(csv_content)  # Validate CSV format

        dataset = self.uow.datasets.create(name=name, description=description)
        if not dataset or not dataset.id:
            raise ValueError("Failed to create dataset")

        datapoints_created = 0
        if csv_content.strip():
            parsed_datapoints = self.parse_csv_content(csv_content)
            for dp in parsed_datapoints:
                dp["dataset_id"] = dataset.id

            if parsed_datapoints:
                self.uow.datapoints.bulk_create(parsed_datapoints)
                datapoints_created = len(parsed_datapoints)

        return {"id": dataset.id, "name": dataset.name, "datapoints_created": datapoints_created}

    def delete_dataset(self, dataset_id: int) -> bool:
        success = self.uow.datasets.delete(dataset_id)
        if not success:
            raise ValueError(f"Dataset with id {dataset_id} not found")
        return success
