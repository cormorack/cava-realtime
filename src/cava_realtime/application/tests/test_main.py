"""Test cava_realtime.application.main.app."""


def test_health(app, service_id):
    """Test /healthz endpoint."""
    response = app.get(f"/{service_id}/healthz")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong!"}


def test_metrics(app, service_id):
    """Test /healthz endpoint."""
    response = app.get(f"/{service_id}/metrics")
    assert response.status_code == 200


def test_home(app):
    """Test /healthz endpoint."""
    response = app.get("/")
    assert response.status_code == 200
