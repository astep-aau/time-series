from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from time_series.outlier_detection_api.routes import analyze

app = FastAPI(
    title="Outlier Detection API",
    description="API for running outlier detection",
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


app.include_router(analyze.router, prefix="/analyze", tags=["Analyze"])
