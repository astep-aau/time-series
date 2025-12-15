# TODO fix this file so it work with the uploaded dataset.
import logging

from fastapi import FastAPI, Query
from pydantic import BaseModel

logger = logging.getLogger("rest-api")
app = FastAPI()


class prediction_query(BaseModel):
    name: str = Query(description="Name of the user")
    date: str = Query(description="Date in ISO format.")
    city: str = Query(description="City name.")
    user_data: list = Query(description="Energy readings from the user in chronological order.")
