"""CAVA Realtime API settings."""

import pydantic


class ApiSettings(pydantic.BaseSettings):
    """FASTAPI application settings."""

    name: str = "CAVA Realtime"
    service_id: str = "realtime"
    cors_origins: str = "*"
    cachecontrol: str = "public, max-age=3600"
    debug: bool = False

    lower_case_query_parameters: bool = False

    # Kafka Settings
    kafka_host: str = 'localhost'
    kafka_port: str = '9092'

    @pydantic.validator("cors_origins")
    def parse_cors_origin(cls, v):
        """Parse CORS origins."""
        return [origin.strip() for origin in v.split(",")]

    class Config:
        """model config"""

        env_file = ".env"
        env_prefix = "CR_API_"


api_config = ApiSettings()
