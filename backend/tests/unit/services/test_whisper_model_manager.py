import pytest
from unittest.mock import Mock, patch
from app.services.whisper_service import WhisperModelManager, STANDARD_MODELS


class TestWhisperModelManager:
    def test_init(self):
        manager = WhisperModelManager()
        assert manager.loaded_models == {}
        assert manager.model_dir.exists()

    def test_get_available_models(self):
        manager = WhisperModelManager()
        models = manager.get_available_models()
        # 標準モデルが含まれていることを確認
        for model in STANDARD_MODELS:
            assert model in models
        assert len(models) >= len(STANDARD_MODELS)
        assert "base" in models
        assert "tiny" in models

    def test_is_valid_model(self):
        manager = WhisperModelManager()

        # 有効なモデル
        assert manager.is_valid_model("base") is True
        assert manager.is_valid_model("tiny") is True
        assert manager.is_valid_model("large-v3") is True

        # 無効なモデル
        assert manager.is_valid_model("invalid") is False
        assert manager.is_valid_model("") is False
        assert manager.is_valid_model("large-v999") is False

    @patch("app.services.whisper_service.whisper.load_model")
    def test_load_model_success(self, mock_load_model):
        mock_model = Mock()
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()
        result = manager.load_model("base")

        assert result == mock_model
        assert "base" in manager.loaded_models
        mock_load_model.assert_called_once()

    @patch("app.services.whisper_service.whisper.load_model")
    def test_load_model_invalid(self, mock_load_model):
        manager = WhisperModelManager()

        with pytest.raises(ValueError) as exc_info:
            manager.load_model("invalid_model")

        assert "Invalid model name" in str(exc_info.value)
        mock_load_model.assert_not_called()

    @patch("app.services.whisper_service.whisper.load_model")
    def test_load_model_cached(self, mock_load_model):
        mock_model = Mock()
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()

        # 1回目のロード
        result1 = manager.load_model("base")
        # 2回目のロード（キャッシュから取得）
        result2 = manager.load_model("base")

        assert result1 == result2
        assert result1 == mock_model
        mock_load_model.assert_called_once()  # 1回だけ呼ばれる

    @patch("app.services.whisper_service.whisper.load_model")
    def test_transcribe_success(self, mock_load_model):
        mock_model = Mock()
        mock_model.transcribe.return_value = {
            "text": "  Hello world  ",
            "language": "en",
            "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
        }
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()
        result = manager.transcribe("test_audio.wav", "base")

        assert result["text"] == "Hello world"  # strip()されている
        assert result["language"] == "en"
        assert result["model_used"] == "base"
        assert len(result["segments"]) == 1

    @patch("app.services.whisper_service.whisper.load_model")
    def test_transcribe_invalid_model(self, mock_load_model):
        manager = WhisperModelManager()

        with pytest.raises(ValueError) as exc_info:
            manager.transcribe("test_audio.wav", "invalid_model")

        assert "Invalid model name" in str(exc_info.value)
        mock_load_model.assert_not_called()

    @patch("app.services.whisper_service.whisper.load_model")
    def test_transcribe_failure(self, mock_load_model):
        mock_model = Mock()
        mock_model.transcribe.side_effect = Exception("Transcription error")
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()

        with pytest.raises(Exception) as exc_info:
            manager.transcribe("test_audio.wav", "base")

        assert "Transcription failed" in str(exc_info.value)
