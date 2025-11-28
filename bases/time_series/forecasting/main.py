import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from time_series.forecast import get_all_datasets, predict

logger = logging.getLogger("rest-api")
app = FastAPI()


class prediction_query(BaseModel):
    name: str = Query(description="Name of the user")
    date: str = Query(description="Date in ISO format.")
    city: str = Query(description="City name.")
    user_data: list = Query(description="Energy readings from the user in chronological order.")


@app.post("/predict")
def create_dataset_endpoint(query: prediction_query) -> list:
    try:
        parsed_date = datetime.fromisoformat(query.date)
        print(parsed_date)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid start_date format: {query.date}. Expected ISO format.",
        )
    try:
        predicted_values = predict(user_data=query.user_data, city=query.city)
        # add_prediction(name=query.name, date=parsed_date, user_data=query, prediction=predicted_values) #TODO:
        return predicted_values
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predict/all")
def get_all_predictions() -> dict:
    return {"datasets": get_all_datasets()}
