from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_available_models():
    response = client.get("/models")

    assert response.status_code == 200
    data = response.json()

    assert "available_models" in data
    assert isinstance(data["available_models"], list)
    assert len(data["available_models"]) > 0
    assert "base" in data["available_models"]
    assert "tiny" in data["available_models"]
