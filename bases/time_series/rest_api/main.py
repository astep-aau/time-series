import logging

from fastapi import FastAPI
from time_series.greeting import hello_world

logger = logging.getLogger("rest-api")
app = FastAPI()


@app.get("/")
def root() -> dict:
    logger.info("fastapi root endpoint was called")
    return {"message": hello_world()}
