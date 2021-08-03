"""``pytest`` configuration."""

import pytest

from starlette.testclient import TestClient


@pytest.fixture
def service_id() -> str:
    from cava_realtime.application.settings import api_config
    return api_config.service_id


@pytest.fixture
def set_env(monkeypatch):
    ...


@pytest.fixture(autouse=True)
def app(set_env) -> TestClient:
    """Create App."""
    from cava_realtime.application.main import app

    return TestClient(app)
