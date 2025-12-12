from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SQLAEnum
from sqlmodel import Field, Relationship, SQLModel


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"
    __table_args__ = {"schema": "timeseries"}

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=255, index=True)
    description: Optional[str] = None

    datapoints: list["Datapoint"] = Relationship(back_populates="dataset", cascade_delete=True)
    analyses: list["Analysis"] = Relationship(back_populates="dataset", cascade_delete=True)


class Datapoint(SQLModel, table=True):
    __tablename__ = "datapoints"
    __table_args__ = {"schema": "timeseries"}

    dataset_id: int = Field(foreign_key="timeseries.datasets.id", primary_key=True)
    time: datetime = Field(primary_key=True)
    value: float

    dataset: Optional[Dataset] = Relationship(back_populates="datapoints")


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"
    __table_args__ = {"schema": "timeseries"}

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="timeseries.datasets.id", index=True)
    detection_method: str = Field(max_length=255)
    name: str = Field(max_length=255)
    description: Optional[str] = None

    dataset: Optional[Dataset] = Relationship(back_populates="analyses")
    anomalies: list["Anomaly"] = Relationship(back_populates="analysis", cascade_delete=True)


class AnomalyType(str, Enum):
    point = "point"
    contextual = "contextual"


class StatusType(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    error = "error"


class Anomaly(SQLModel, table=True):
    __tablename__ = "anomalies"
    __table_args__ = {"schema": "timeseries"}

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="timeseries.analyses.id", index=True)
    start: datetime
    end: datetime
    validated: bool = Field(default=False)
    type: AnomalyType = Field(sa_column=Column(SQLAEnum(AnomalyType, name="anomalytype", schema="timeseries")))
    status: StatusType = Field(
        default=StatusType.pending,
        sa_column=Column(SQLAEnum(StatusType, name="statustype", schema="timeseries")),
    )
    analysis: Optional[Analysis] = Relationship(back_populates="anomalies")
