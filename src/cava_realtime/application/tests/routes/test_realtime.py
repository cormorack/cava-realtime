"""Test cava_realtime.application.routers.realtime."""


def test_sources(app, service_id):
    """Test /healthz endpoint."""
    response = app.get(f"/{service_id}/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list) is True
