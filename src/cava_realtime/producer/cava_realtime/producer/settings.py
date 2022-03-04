from pydantic import BaseSettings
from typing import List


class ProducerSettings(BaseSettings):
    """Application settings."""

    development: bool = False

    # OOI M2M Settings
    ooi_username: str
    ooi_token: str

    # Kafka Settings
    kafka_host: str = 'localhost'
    kafka_port: str = '9092'

    # CAVA API Settings
    metadata_url: str = 'https://api-development.ooica.net/metadata'

    # Dev Instruments
    dev_instruments: List[str] = [
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

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CR_PRODUCER_"


producer_settings = ProducerSettings()
