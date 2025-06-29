import pytest
from unittest.mock import Mock, MagicMock
from app.main import app
from app.api.dependencies import WhisperService, get_whisper_service


@pytest.fixture
def mock_whisper_service():
    """WhisperServiceのモックを作成"""
    mock_service = Mock(spec=WhisperService)
    mock_service.model_manager = Mock()
    mock_service.model_manager.loaded_models = {}
    
    # 基本的なメソッドのデフォルト戻り値を設定
    mock_service.get_available_models.return_value = ["tiny", "base", "small", "medium", "large"]
    mock_service.is_valid_model.return_value = True
    mock_service.load_model.return_value = MagicMock()
    mock_service.transcribe.return_value = {
        "text": "Test transcription",
        "language": "en",
        "segments": [],
        "model_used": "base",
    }
    mock_service.get_model_status.return_value = {
        "model": "base",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": False,
        "message": "Model is available but not loaded yet",
    }
    
    return mock_service


@pytest.fixture
def override_whisper_service(mock_whisper_service):
    """WhisperServiceの依存性注入をオーバーライド"""
    app.dependency_overrides[get_whisper_service] = lambda: mock_whisper_service
    yield mock_whisper_service
    app.dependency_overrides.clear()