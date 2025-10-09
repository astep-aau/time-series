from pprint import pprint

from sqlmodel import Session, SQLModel, create_engine, select
from time_series.model import TimeSeries


def main() -> None:
    example_00 = TimeSeries(dataset="A-1", column=0, row=0, data=1.0)
    example_01 = TimeSeries(dataset="A-1", column=0, row=1, data=0)
    example_02 = TimeSeries(dataset="A-1", column=0, row=2, data=0)

    example_10 = TimeSeries(dataset="A-1", column=1, row=0, data=0.66)
    example_11 = TimeSeries(dataset="A-1", column=1, row=1, data=0)
    example_12 = TimeSeries(dataset="A-1", column=1, row=2, data=0)

    engine = create_engine("sqlite:///database.db")

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(example_00)
        session.add(example_01)
        session.add(example_02)
        session.add(example_10)
        session.add(example_11)
        session.add(example_12)
        session.commit()

        statement = select(TimeSeries).where(TimeSeries.dataset == "A-1")
        time_series = session.exec(statement).all()
        pprint(time_series)
