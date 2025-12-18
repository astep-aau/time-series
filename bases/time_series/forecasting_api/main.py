from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from time_series.forecasting_api.routes import forecasting
from time_series.uvicorn_runner.logging_utils import setup_logging

setup_logging()

app = FastAPI(
    title="forecasting",
    description="API for running forecasting",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
def health_check():
    return "OK"


app.include_router(forecasting.router, prefix="/forecasting", tags=["forecasting"])

add_pagination(app)
