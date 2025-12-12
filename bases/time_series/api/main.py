from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from time_series.api.routes import analyses, datasets

app = FastAPI(
    title="Time Series API",
    description="API for managing time series datasets, forecasting and outlier detection",
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


app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
app.include_router(analyses.router, prefix="/analyses", tags=["Analyses"])

add_pagination(app)
