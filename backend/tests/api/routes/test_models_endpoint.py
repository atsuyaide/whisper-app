from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_available_models(override_whisper_service):
    """利用可能なモデル一覧取得テスト"""
    mock_service = override_whisper_service
    mock_service.get_available_models.return_value = ["tiny", "base", "small", "medium", "large"]

    response = client.get("/models")

    assert response.status_code == 200
    data = response.json()
    assert "available_models" in data
    assert isinstance(data["available_models"], list)
    assert len(data["available_models"]) == 5
    assert "tiny" in data["available_models"]
    assert "base" in data["available_models"]