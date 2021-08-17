
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from prometheus_fastapi_instrumentator import Instrumentator

from cava_realtime.application.settings import api_config
from cava_realtime.application.routers import realtime

SERVICE_ID = api_config.service_id

app = FastAPI(
    title=api_config.name,
    openapi_url=f"/{SERVICE_ID}/openapi.json",
    docs_url=f"/{SERVICE_ID}/",
    redoc_url=None,
    version="0.1.0",
    description="Realtime service for Interactive Oceans.",
)

if api_config.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["*"],
    )


@app.get(f"/{SERVICE_ID}/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


app.include_router(
    realtime.router, prefix=f"/{SERVICE_ID}", tags=[f"{SERVICE_ID}"]
)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url=f"/{SERVICE_ID}")


# Prometheus instrumentation
Instrumentator().instrument(app).expose(
    app, endpoint=f"/{SERVICE_ID}/metrics", include_in_schema=False
)
