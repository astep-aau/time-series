import os

from dotenv import load_dotenv
from sqlmodel import create_engine

load_dotenv()


DATABASE_URL = "postgresql://%s:%s@%s:%s/%s" % (
    os.environ["DB_USER"],
    os.environ["DB_PASS"],
    os.environ["DB_HOST"],
    os.environ["DB_PORT"],
    os.environ["DB_NAME"],
)

ENGINE = create_engine(
    DATABASE_URL,
    echo=not bool(os.environ["PRODUCTION_MODE"]),
)
