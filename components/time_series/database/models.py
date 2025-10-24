from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=255, index=True)
    start_date: datetime
    description: Optional[str] = None

    datapoints: list["Datapoint"] = Relationship(back_populates="dataset", cascade_delete=True)
    anomalies: list["Anomaly"] = Relationship(back_populates="dataset", cascade_delete=True)


class Datapoint(SQLModel, table=True):
    __tablename__ = "datapoints"

    dataset_id: int = Field(foreign_key="datasets.id", primary_key=True)
    time: datetime = Field(primary_key=True)
    value: float

    dataset: Optional[Dataset] = Relationship(back_populates="datapoints")


class AnomalyType(str, Enum):
    point = "point"
    contextual = "contextual"


class Anomaly(SQLModel, table=True):
    __tablename__ = "anomalies"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id")
    start_idx: datetime
    end_idx: datetime
    type: AnomalyType
    validated: bool = Field(default=False)

    dataset: Optional["Dataset"] = Relationship(back_populates="anomalies")
