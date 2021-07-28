
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from loguru import logger

from confluent_kafka import Consumer

from cava_realtime.application.settings import api_config
from cava_realtime.application.store import AVAILABLE_TOPICS
from cava_realtime.application.routers import realtime

SERVICE_ID = "realtime"

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


@app.get("/healthz", description="Health Check", tags=["Health Check"])
def ping():
    """Health check."""
    return {"ping": "pong!"}


@app.on_event("startup")
def startup_event():
    logger.info("Get available topics.")
    conf = realtime.KAFKA_CONF.copy()
    conf.update({'group.id': 'admin'})

    consumer = Consumer(conf)
    cluster_meta = consumer.list_topics()
    AVAILABLE_TOPICS.update(
        {
            k: v
            for k, v in cluster_meta.topics.items()
            if '__consumer_offsets' not in k
        }
    )
    logger.info(f"Number of topics available: {len(AVAILABLE_TOPICS.keys())}.")


app.include_router(
    realtime.router, prefix=f"/{SERVICE_ID}", tags=[f"{SERVICE_ID}"]
)


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/realtime")
