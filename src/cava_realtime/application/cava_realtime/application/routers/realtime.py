from fastapi import APIRouter, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from streamz import Stream
import json
from uuid import uuid4

from cava_realtime.application.settings import api_config
from cava_realtime.application.routers.utils import get_available_topics

try:
    from importlib.resources import files as resources_files  # type: ignore
except ImportError:
    # Try backported to PY<39 `importlib_resources`.
    from importlib_resources import files as resources_files  # type: ignore

KAFKA_CONF = {
    'bootstrap.servers': f'{api_config.kafka_host}:{api_config.kafka_port}'  # noqa
}
router = APIRouter()
templates = Jinja2Templates(
    directory=str(resources_files(__package__) / "templates")
)


@router.get("/sources")
def get_sources():
    available_topics = get_available_topics(KAFKA_CONF)

    return list(
        map(
            lambda k: k.replace('__raw', ''),
            available_topics.keys(),
        )
    )


@router.get("/test/{ref}", response_class=HTMLResponse)
async def test_websocket(request: Request, ref: str):
    return templates.TemplateResponse(
        "realtime-test.html", {"request": request, "ref": ref}
    )


@router.websocket_route('/{ref}')
class WebsocketConsumer(WebSocketEndpoint):
    """
    Consume messages from ref>
    This will start a Kafka Consumer from a topic
    And this path operation will:
    * return ConsumerResponse
    """

    async def on_connect(self, websocket: WebSocket) -> None:
        ref = websocket["path"].split('/')[2]
        logger.info(ref)

        await websocket.accept()
        await websocket.send_json(
            {"status": "accepted", "message": "connected"}
        )
        available_topics = get_available_topics(KAFKA_CONF)
        topicname = f"{ref}__raw"
        if topicname in available_topics:
            await websocket.send_json(
                {
                    "status": "success",
                    "message": f"consumer connected for {topicname}"
                }
            )
            logger.info(f"Connected to {ref}")
            uid = uuid4().hex

            conf = KAFKA_CONF.copy()
            conf.update({'group.id': uid, 'auto.offset.reset': 'earliest'})

            self.stream = Stream.from_kafka(
                [topicname],
                conf,
            )
            self.stream_json = self.stream.map(json.loads).sink(
                self.send_consumer_message, websocket
            )
            self.stream_json.start()
        else:
            self.stream = None
            self.stream_json = None
            message = f"{ref} not found."
            logger.warning(message)
            await websocket.send_json({"status": "error", "message": message})

    async def on_disconnect(
        self, websocket: WebSocket, close_code: int
    ) -> None:
        if self.stream_json:
            self.stream_json.destroy()

        if self.stream:
            self.stream._close_consumer()
        logger.info("Disconnected")

    async def send_consumer_message(
        self,
        data: dict,
        websocket: WebSocket,
    ) -> None:
        await websocket.send_json(data)
