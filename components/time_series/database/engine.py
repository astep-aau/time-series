import os

from sqlmodel import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://group9_user:lI4_yb59YfP@cs-astep02.srv.aau.dk:30432/group9_db")

engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
)
