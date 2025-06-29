import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_whisper_manager():
    """WhisperModelManagerのモック"""
    with patch("app.services.whisper_service.whisper_manager") as mock:
        mock.get_available_models.return_value = ["tiny", "base", "my-custom-model"]
        mock.is_valid_model.return_value = True
        mock.loaded_models = {}
        yield mock


def test_get_model_info_custom_model(mock_whisper_manager):
    """カスタムモデル情報取得テスト"""
    # 実際のAPIエンドポイントをテストして、実際の結果と比較
    response = client.get("/models/my-custom-model/info")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "my-custom-model"
    assert data["exists"] is True
    assert data["is_custom"] is True
    assert data["type"] == "custom"
    # 実際のファイルパスが設定されている
    assert "my-custom-model.pt" in data["file_path"]
    assert data["file_size"] > 0


def test_get_model_info_standard_model(mock_whisper_manager):
    """標準モデル情報取得テスト"""
    mock_whisper_manager.get_model_info.return_value = {
        "model": "base",
        "exists": True,
        "is_custom": False,
        "is_loaded": False,
        "type": "standard",
    }

    response = client.get("/models/base/info")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "base"
    assert data["exists"] is True
    assert data["is_custom"] is False
    assert data["type"] == "standard"
    assert data["file_path"] is None
    assert data["file_size"] is None


def test_get_model_info_nonexistent_model(mock_whisper_manager):
    """存在しないモデル情報取得テスト"""
    mock_whisper_manager.get_model_info.return_value = {
        "model": "nonexistent",
        "exists": False,
        "message": "Model not found. Available models: ['tiny', 'base', 'my-custom-model']",
    }

    response = client.get("/models/nonexistent/info")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "nonexistent"
    assert data["exists"] is False
    assert "not found" in data["message"]


def test_model_status_with_custom_flag(mock_whisper_manager):
    """カスタムフラグ付きモデルステータステスト"""
    mock_whisper_manager.get_model_status.return_value = {
        "model": "my-custom-model",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": True,
        "message": "Custom model is available but not loaded yet",
    }

    response = client.get("/models/my-custom-model/status")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "my-custom-model"
    assert data["is_custom"] is True
    assert "Custom" in data["message"]


def test_models_list_includes_custom_models(mock_whisper_manager):
    """モデル一覧にカスタムモデルが含まれることを確認"""
    mock_whisper_manager.get_available_models.return_value = [
        "base",
        "tiny",
        "my-custom-model",
        "japanese-news-v1",
    ]

    response = client.get("/models")

    assert response.status_code == 200
    data = response.json()
    models = data["available_models"]

    # 標準モデルが含まれている
    assert "base" in models
    assert "tiny" in models

    # カスタムモデルが含まれている
    assert "my-custom-model" in models
    assert "japanese-news-v1" in models
