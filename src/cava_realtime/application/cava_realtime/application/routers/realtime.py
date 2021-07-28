from fastapi import APIRouter
from fastapi import WebSocket
from loguru import logger
from starlette.endpoints import WebSocketEndpoint
from streamz import Stream
import json

from cava_realtime.application.settings import api_config
from cava_realtime.application.store import AVAILABLE_TOPICS

KAFKA_CONF = {
    'bootstrap.servers': f'{api_config.kafka_host}:{api_config.kafka_port}'  # noqa
}
router = APIRouter()


@router.get("/sources")
def get_sources():

    return list(
        map(
            lambda k: k.replace('__raw', ''),
            AVAILABLE_TOPICS.keys(),
        )
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

        topicname = f"{ref}__raw"
        if topicname in AVAILABLE_TOPICS:
            await websocket.send_json(
                {"status": "success", "message": "consumer connected"}
            )
            logger.info(f"Connected to {ref}")

            conf = KAFKA_CONF.copy()
            conf.update({'group.id': 'ctd_group'})

            stream = Stream.from_kafka(
                [topicname],
                conf,
            )
            self.stream_json = stream.map(json.loads).sink(
                self.send_consumer_message, websocket
            )
            self.stream_json.start()
        else:
            self.stream_json = None
            message = f"{ref} not found."
            logger.warning(message)
            await websocket.send_json({"status": "error", "message": message})

    async def on_disconnect(
        self, websocket: WebSocket, close_code: int
    ) -> None:
        if self.stream_json:
            self.stream_json.destroy()
        logger.info("Disconnected")

    async def send_consumer_message(
        self,
        data: dict,
        websocket: WebSocket,
    ) -> None:
        await websocket.send_json(data)
