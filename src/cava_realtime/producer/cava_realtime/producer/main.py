import requests
import typer
from loguru import logger
from kafka import KafkaProducer
from cava_realtime.producer.models.stream import StreamProducer
from cava_realtime.producer.models.obs import ObsProducer
from cava_realtime.producer.settings import producer_settings

KAFKA_HOST = producer_settings.kafka_host
KAFKA_PORT = producer_settings.kafka_port
DEVELOPMENT = producer_settings.development
# setup the base url for the request that will be built using the inputs above.
BASE_URL = "https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv"
app = typer.Typer()


def fetch_instruments_catalog():
    try:
        req = requests.get(
            f"{producer_settings.metadata_url.strip('/')}/get_instruments_catalog"  # noqa
        )
        instruments_catalog = req.json()
    except Exception:
        logger.warning(req.status_code)
        instruments_catalog = None

    return instruments_catalog


@app.command(help="Start streaming data into provided kafka cluster.")
def stream():
    instruments_catalog = fetch_instruments_catalog()
    logger.info(f"{KAFKA_HOST}:{KAFKA_PORT}")
    producer = KafkaProducer(bootstrap_servers=f"{KAFKA_HOST}:{KAFKA_PORT}")
    if DEVELOPMENT is True:
        instruments_catalog = [
            i
            for i in instruments_catalog
            if i["data_table"]
            in [
                "RS03AXBS-LJ03A-12-CTDPFB301-streamed-ctdpf_optode_sample",
                "RS01SLBS-LJ01A-12-CTDPFB101-streamed-ctdpf_optode_sample",
                "RS01SBPS-PC01A-4A-CTDPFA103-streamed-ctdpf_optode_sample",
                "RS03AXPS-SF03A-2A-CTDPFA302-streamed-ctdpf_sbe43_sample",
                "RS03AXPS-PC03A-4A-CTDPFA303-streamed-ctdpf_optode_sample",
                "RS01SBPS-SF01A-2A-CTDPFA102-streamed-ctdpf_sbe43_sample",
                "CE02SHBP-LJ01D-06-CTDBPN106-streamed-ctdbp_no_sample",
                "CE04OSBP-LJ01C-06-CTDBPO108-streamed-ctdbp_no_sample",
                "RS03AXPS-PC03A-4C-FLORDD303-streamed-flort_d_data_record",
                "RS03AXPS-SF03A-3A-FLORTD301-streamed-flort_d_data_record",
                "RS01SBPS-SF01A-3A-FLORTD101-streamed-flort_d_data_record",
                "RS01SBPS-PC01A-4C-FLORDD103-streamed-flort_d_data_record",
            ]
        ]
    realtime_list = [
        StreamProducer(
            **{
                "ref": inst["data_table"],
                "parameters": inst["parameter_rd"].split(","),
                "request_url": "/".join(
                    [
                        BASE_URL,
                        inst["site_rd"],
                        inst["infra_rd"],
                        inst["inst_rd"],
                        inst["stream_method"],
                        inst["stream_rd"],
                    ]
                ),
                "topic": f"{inst['data_table']}__raw",
                "instrument_name": inst["instrument"]["instrument_name"],
                "kafka_producer": producer,
            }
        )
        for inst in instruments_catalog
    ]

    # NOTE: 2021-07-29 -- Not produce iris seismic data right now.
    # realtime_list.append(ObsProducer(kafka_producer=producer))

    for st in realtime_list:
        st.start()

    while all([s.is_alive() for s in realtime_list]):
        continue


if __name__ == "__main__":
    app()
