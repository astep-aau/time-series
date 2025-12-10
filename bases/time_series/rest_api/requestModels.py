from typing import List

from pydantic import BaseModel


class PredictionCreateRequest(BaseModel):
    model_name: str
    dataset_id: int
    city: str
    user_data: List[float]
