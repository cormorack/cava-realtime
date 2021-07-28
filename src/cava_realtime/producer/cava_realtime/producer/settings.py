from pydantic import BaseSettings


class ProducerSettings(BaseSettings):
    """Application settings."""
    development: bool = True

    # OOI M2M Settings
    ooi_username: str
    ooi_token: str

    # Kafka Settings
    kafka_host: str = 'localhost'
    kafka_port: str = '9092'

    # CAVA API Settings
    metadata_url: str = 'https://api-development.ooica.net/metadata'

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CR_PRODUCER_"


producer_settings = ProducerSettings()
