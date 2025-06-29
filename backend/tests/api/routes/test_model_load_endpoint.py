import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app

client = TestClient(app)


def test_load_model_success(override_whisper_service):
    """正常にモデルをロードできる場合のテスト"""
    mock_service = override_whisper_service
    mock_service.load_model.return_value = MagicMock()
    mock_service.model_manager.loaded_models = {}
    mock_service.get_model_status.return_value = {
        "model": "base",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": False,
        "message": "Model is available but not loaded yet",
    }

    response = client.post("/models/base/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "base"
    assert data["is_loaded"] is True
    assert data["load_time"] >= 0.0
    assert "successfully" in data["message"]

    mock_service.load_model.assert_called_once_with("base")


def test_load_model_already_loaded(override_whisper_service):
    """既にロード済みのモデルの場合のテスト"""
    mock_service = override_whisper_service
    mock_service.model_manager.loaded_models = {"base": MagicMock()}
    mock_service.get_model_status.return_value = {
        "model": "base",
        "is_ready": True,
        "is_loaded": True,
        "is_custom": False,
        "message": "Model is already loaded",
    }

    response = client.post("/models/base/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "base"
    assert data["is_loaded"] is True
    assert data["load_time"] == 0.0
    assert "already loaded" in data["message"]

    # load_modelは呼ばれない
    mock_service.load_model.assert_not_called()


def test_load_model_invalid_model_name(override_whisper_service):
    """無効なモデル名の場合のテスト"""
    import pytest
    from app.core.exceptions import InvalidModelError
    
    mock_service = override_whisper_service
    mock_service.is_valid_model.return_value = False
    mock_service.get_available_models.return_value = ["tiny", "base", "small"]

    with pytest.raises(InvalidModelError):
        client.post("/models/invalid_model/load")


def test_load_model_load_failure(override_whisper_service):
    """モデルロードに失敗する場合のテスト"""
    import pytest
    from app.core.exceptions import ModelLoadError
    
    mock_service = override_whisper_service
    mock_service.load_model.side_effect = Exception("Model load failed")
    mock_service.model_manager.loaded_models = {}
    mock_service.get_model_status.return_value = {
        "model": "base",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": False,
        "message": "Model is available but not loaded yet",
    }

    with pytest.raises(ModelLoadError):
        client.post("/models/base/load")


def test_load_model_large_model_load_time(override_whisper_service):
    """大きなモデルのロード時間テスト"""
    import time

    mock_service = override_whisper_service
    
    def slow_load_model(model_name):
        time.sleep(0.1)  # 0.1秒待機
        return MagicMock()
    
    mock_service.load_model.side_effect = slow_load_model
    mock_service.model_manager.loaded_models = {}
    mock_service.get_model_status.return_value = {
        "model": "large",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": False,
        "message": "Model is available but not loaded yet",
    }

    response = client.post("/models/large/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "large"
    assert data["is_loaded"] is True
    assert data["load_time"] >= 0.1


@pytest.mark.parametrize("model_name", ["tiny", "base", "small", "medium", "large"])
def test_load_different_models(model_name, override_whisper_service):
    """異なるモデル名でのロードテスト"""
    mock_service = override_whisper_service
    mock_service.load_model.return_value = MagicMock()
    mock_service.model_manager.loaded_models = {}
    mock_service.get_model_status.return_value = {
        "model": model_name,
        "is_ready": True,
        "is_loaded": False,
        "is_custom": False,
        "message": f"Model {model_name} is available but not loaded yet",
    }

    response = client.post(f"/models/{model_name}/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == model_name
    assert data["is_loaded"] is True

    mock_service.load_model.assert_called_with(model_name)