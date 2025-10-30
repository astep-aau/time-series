import os

from sqlmodel import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5433/timeseriesdb")

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
)
