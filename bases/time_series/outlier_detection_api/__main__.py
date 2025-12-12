from time_series.uvicorn_runner import run

if __name__ == "__main__":
    run(entrypoint="time_series.outlier_detection_api.main:app")
