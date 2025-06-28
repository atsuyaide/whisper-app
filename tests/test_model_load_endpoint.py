import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_whisper_manager():
    """WhisperModelManagerのモック"""
    with patch("app.whisper_service.whisper_manager") as mock:
        mock.get_available_models.return_value = ["tiny", "base", "small"]
        mock.is_valid_model.return_value = True
        mock.loaded_models = {}
        yield mock


def test_load_model_success(mock_whisper_manager):
    """正常にモデルをロードできる場合のテスト"""
    mock_whisper_manager.load_model.return_value = MagicMock()

    response = client.post("/models/base/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "base"
    assert data["is_loaded"] is True
    assert data["load_time"] >= 0.0
    assert "successfully" in data["message"]

    mock_whisper_manager.load_model.assert_called_once_with("base")


def test_load_model_already_loaded(mock_whisper_manager):
    """既にロード済みのモデルの場合のテスト"""
    mock_whisper_manager.loaded_models = {"base": MagicMock()}

    response = client.post("/models/base/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "base"
    assert data["is_loaded"] is True
    assert data["load_time"] == 0.0
    assert "already loaded" in data["message"]

    # load_modelは呼ばれない
    mock_whisper_manager.load_model.assert_not_called()


def test_load_model_invalid_model_name(mock_whisper_manager):
    """無効なモデル名の場合のテスト"""
    mock_whisper_manager.is_valid_model.return_value = False
    mock_whisper_manager.get_available_models.return_value = ["tiny", "base", "small"]

    response = client.post("/models/invalid_model/load")

    assert response.status_code == 400
    data = response.json()
    assert "Invalid model name" in data["detail"]
    assert "invalid_model" in data["detail"]


def test_load_model_load_failure(mock_whisper_manager):
    """モデルロードに失敗した場合のテスト"""
    mock_whisper_manager.load_model.side_effect = Exception("Model loading failed")

    response = client.post("/models/base/load")

    assert response.status_code == 500
    data = response.json()
    assert "Failed to load model base" in data["detail"]
    assert "Model loading failed" in data["detail"]


def test_load_model_large_model_load_time(mock_whisper_manager):
    """大きなモデルのロード時間測定テスト"""
    import time

    def slow_load_model(model_name):
        time.sleep(0.1)  # 0.1秒の遅延をシミュレート
        return MagicMock()

    mock_whisper_manager.load_model.side_effect = slow_load_model

    response = client.post("/models/large/load")

    assert response.status_code == 200
    data = response.json()
    assert data["load_time"] >= 0.1  # 最低0.1秒はかかる
    assert data["load_time"] < 1.0  # 1秒未満で完了


@pytest.mark.parametrize("model_name", ["tiny", "base", "small", "medium", "large"])
def test_load_different_models(mock_whisper_manager, model_name):
    """異なるモデル名でのロードテスト"""
    mock_whisper_manager.load_model.return_value = MagicMock()

    response = client.post(f"/models/{model_name}/load")

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == model_name
    mock_whisper_manager.load_model.assert_called_with(model_name)


def test_load_model_response_schema():
    """レスポンススキーマの妥当性テスト"""
    with patch("app.whisper_service.whisper_manager") as mock:
        mock.is_valid_model.return_value = True
        mock.loaded_models = {}
        mock.load_model.return_value = MagicMock()

        response = client.post("/models/base/load")

        assert response.status_code == 200
        data = response.json()

        # 必要なフィールドが存在することを確認
        required_fields = ["model", "is_loaded", "load_time", "message"]
        for field in required_fields:
            assert field in data

        # データ型の確認
        assert isinstance(data["model"], str)
        assert isinstance(data["is_loaded"], bool)
        assert isinstance(data["load_time"], (int, float))
        assert isinstance(data["message"], str)
