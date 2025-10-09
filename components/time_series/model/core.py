from sqlmodel import Field, SQLModel


class TimeSeries(SQLModel, table=True):
    dataset: str = Field(primary_key=True)
    column: int = Field(primary_key=True)
    row: int = Field(primary_key=True)
    data: float
