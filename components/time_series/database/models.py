from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


# Dataset model
class Dataset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=255, index=True)
    start_date: datetime
    description: Optional[str] = None

    # Relationship
    datapoints: list["Datapoint"] = Relationship(back_populates="dataset", cascade_delete=True)


# Datapoint model
class Datapoint(SQLModel, table=True):
    dataset_id: int = Field(foreign_key="dataset.id", primary_key=True)
    time: datetime = Field(primary_key=True)
    value: float

    # Relationship
    dataset: Optional[Dataset] = Relationship(back_populates="datapoints")
