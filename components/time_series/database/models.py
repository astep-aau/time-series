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
    analyses: list["Analysis"] = Relationship(back_populates="dataset", cascade_delete=True)


class Datapoint(SQLModel, table=True):
    __tablename__ = "datapoints"

    dataset_id: int = Field(foreign_key="datasets.id", primary_key=True)
    time: datetime = Field(primary_key=True)
    value: float

    dataset: Optional[Dataset] = Relationship(back_populates="datapoints")


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: int = Field(foreign_key="datasets.id", index=True)
    model: str = Field(max_length=255)
    name: str = Field(max_length=255)
    description: Optional[str] = None

    dataset: Optional[Dataset] = Relationship(back_populates="analyses")
    anomalies: list["Anomaly"] = Relationship(back_populates="analysis", cascade_delete=True)
    predictions: list["Prediction"] = Relationship(back_populates="analyses", cascade_delete=True)


class AnomalyType(str, Enum):
    point = "point"
    contextual = "contextual"


class Anomaly(SQLModel, table=True):
    __tablename__ = "anomalies"

    id: Optional[int] = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analyses.id", index=True)
    start: datetime
    end: datetime
    type: AnomalyType
    validated: bool = Field(default=False)

    analysis: Optional[Analysis] = Relationship(back_populates="anomalies")


# class PredictionDataset(SQLModel, table=True):
#     __tablename__ = "predictions"

#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(unique=True, max_length=255, index=True)
#     date: datetime
#     datapoints: list["PredictionDatapoint"] = Relationship(back_populates="predictions", cascade_delete=True)
#     results: list["PredictionResult"] = Relationship(back_populates="predictions", cascade_delete=True)


# class Predictionatapoint(SQLModel, table=True):
#     __tablename__ = "prediction_datapoints"

#     dataset_id: int = Field(foreign_key="predictions.id", primary_key=True)
#     time: datetime = Field(primary_key=True)
#     value: float
#     dataset: Optional[PredictionDataset] = Relationship(back_populates="predictions")


class Prediction(SQLModel, table=True):
    __tablename__ = "prediction_results"

    analysis_id: int = Field(foreign_key="analyses.id", primary_key=True)
    time: datetime = Field(primary_key=True)
    value: float

    dataset: Optional[Analysis] = Relationship(back_populates="predictions")
