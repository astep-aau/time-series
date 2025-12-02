from sqlmodel import Field, SQLModel


class TimeSeries(SQLModel, table=True):
    __table_args__ = {"schema": "timeseries"}
    dataset: str = Field(primary_key=True)
    column: int = Field(primary_key=True)
    row: int = Field(primary_key=True)
    data: float
