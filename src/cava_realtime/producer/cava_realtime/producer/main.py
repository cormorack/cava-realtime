import httpx
import typer
import pendulum
import asyncio
import time
from loguru import logger
from kafka import KafkaProducer
from cava_realtime.producer.models.stream import StreamProducer
from typing import Optional, Dict, Any

# from cava_realtime.producer.models.obs import ObsProducer
from cava_realtime.producer.settings import producer_settings

KAFKA_HOST = producer_settings.kafka_host
KAFKA_PORT = producer_settings.kafka_port
DEVELOPMENT = producer_settings.development
API_USERNAME = producer_settings.ooi_username
API_TOKEN = producer_settings.ooi_token
# setup the base url for the request that will be built using the inputs above.
BASE_URL = "https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv"
app = typer.Typer()


def fetch_instruments_catalog():
    try:
        req = httpx.get(
            f"{producer_settings.metadata_url.strip('/')}/get_instruments_catalog"  # noqa
        )
        instruments_catalog = req.json()
    except Exception:
        logger.warning(req.status_code)
        instruments_catalog = None

    return instruments_catalog


async def check_live_stream(
    inst: Dict[str, Any], client: Optional[httpx.AsyncClient] = None
) -> Optional[Dict[str, Any]]:
    url = '/'.join(
        [
            BASE_URL,
            inst['site_rd'],
            inst['infra_rd'],
            inst['inst_rd'],
            "metadata",
            "times",
        ]
    )
    if client is not None:
        resp = await client.get(url)
    else:
        resp = await httpx.get(
            url,
            auth=(API_USERNAME, API_TOKEN),
        )
    if resp.status_code == 200:
        try:
            stream_list = resp.json()
            if len(stream_list) > 0:
                stream = next(
                    filter(
                        lambda st: st['stream'] == inst['stream_rd']
                        and st['method'] == inst['stream_method'],
                        stream_list,
                    )
                )
                stream_end = pendulum.parse(stream['endTime'])
                now = pendulum.now(tz=stream_end.timezone_name)
                if stream_end.year >= now.year:
                    return inst
        except Exception as e:
            logger.error(e)
    return None


async def get_streaming_instruments(instruments_catalog, client):
    coros = [
        check_live_stream(inst, client=client)
        for inst in instruments_catalog
        if inst.get('stream_method') == 'streamed'
    ]
    results = await asyncio.gather(*coros)
    streamed_instruments = [r for r in results if r is not None]
    return streamed_instruments


async def start_rt(rt):
    task = None
    while True:
        refdes = rt.ref
        if task is None or task.done() is True:
            logger.debug(f"Sending a new task for {refdes}")
            task = asyncio.create_task(rt.request_data())
        else:
            logger.debug(f"Waiting data for {refdes}")
        # Only request every 5 seconds
        await asyncio.sleep(10)


async def run_producer(realtime_list):
    logger.info("Producer is running.")
    coros = [start_rt(rt) for rt in realtime_list]
    await asyncio.gather(*coros)


@app.command(help="Start streaming data into provided kafka cluster.")
def stream(disable_kafka: bool = False):
    logger.info("Streaming producer starting.")
    instruments_catalog = fetch_instruments_catalog()
    producer = None
    if disable_kafka is False:
        ready = False
        while not ready:
            try:
                producer = KafkaProducer(
                    bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}"
                )
                ready = True
            except Exception as e:
                logger.warning(e)
                time.sleep(10)
        logger.info("Connected to kafka. ({KAFKA_HOST}:{KAFKA_PORT})")
    else:
        logger.info("Kafka connection disabled.")

    if producer_settings.development:
        logger.info("Development mode enabled.")

    # NOTE: 2021-07-29 -- Not produce iris seismic data right now.
    # realtime_list.append(ObsProducer(kafka_producer=producer))

    loop = asyncio.get_event_loop()
    limits = httpx.Limits(max_connections=10)
    client = httpx.AsyncClient(auth=(API_USERNAME, API_TOKEN), limits=limits)

    # streamed_instruments = loop.run_until_complete(
    #     get_streaming_instruments(instruments_catalog, client)
    # )
    realtime_list = []
    for inst in instruments_catalog:
        if inst.get('stream_method') == 'streamed':
            if not any(
                s in inst['stream_rd']
                # Filter these streams!
                for s in [
                    '15s',
                    '24hr',
                    'configuration',
                    'coefficients',
                    'engineering',
                    'settings',
                    '_cal',
                    'data_header',
                    'voltage',
                    'metadata',
                    'config',
                    'status',
                    'hardware',
                    'leveling',
                    'identification_string',
                    'ancillary_system_data',
                    'transmit_path',
                    'test',
                    'dev',
                    'clock_data',
                    'motor_current',
                    'event_counter',
                    'reference',
                    'dark_sample'
                ]
            ):
                refdes = inst['data_table']
                if DEVELOPMENT is True:
                    if refdes not in producer_settings.dev_instruments:
                        continue
                stream_producer = StreamProducer(
                    **{
                        'ref': inst['data_table'],
                        'parameters': inst['parameter_rd'].split(','),
                        'request_url': '/'.join(
                            [
                                BASE_URL,
                                inst['site_rd'],
                                inst['infra_rd'],
                                inst['inst_rd'],
                                inst['stream_method'],
                                inst['stream_rd'],
                            ]
                        ),
                        'topic': f"{inst['data_table']}__raw",
                        'instrument_name': inst['instrument']['instrument_name'],
                        'kafka_producer': producer,
                        'client': client,
                    }
                )
                realtime_list.append(stream_producer)
    logger.info(
        f"{len(realtime_list)} streams will be fetched."  # noqa
    )
    loop.run_until_complete(run_producer(realtime_list))


if __name__ == "__main__":
    app()
