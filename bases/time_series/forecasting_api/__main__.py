from time_series.uvicorn_runner import run

if __name__ == "__main__":
    run(entrypoint="time_series.forecasting_api.main:app")
