from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


def test_transcribe_audio_success(override_whisper_service):
    """正常な音声ファイルの文字起こしテスト"""
    mock_service = override_whisper_service
    mock_service.transcribe.return_value = {
        "text": "Hello world",
        "language": "en", 
        "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
        "model_used": "base",
    }

    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}

    response = client.post("/transcribe", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_audio.wav"
    assert data["content_type"] == "audio/wav"
    assert data["file_size"] == len(fake_audio_data)
    assert data["status"] == "completed"
    assert data["transcription"]["text"] == "Hello world"
    assert data["transcription"]["language"] == "en"
    assert data["transcription"]["model_used"] == "base"


def test_transcribe_audio_with_model_selection(override_whisper_service):
    """モデル選択付き文字起こしテスト"""
    mock_service = override_whisper_service
    mock_service.transcribe.return_value = {
        "text": "Hello world",
        "language": "en",
        "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
        "model_used": "tiny",
    }

    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}
    data = {"model": "tiny"}

    response = client.post("/transcribe", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["transcription"]["model_used"] == "tiny"


def test_transcribe_audio_invalid_model(override_whisper_service):
    """無効なモデル名の場合のテスト"""
    import pytest
    from app.core.exceptions import InvalidModelError
    
    mock_service = override_whisper_service
    mock_service.is_valid_model.return_value = False
    mock_service.get_available_models.return_value = ["tiny", "base", "small"]

    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}
    data = {"model": "invalid_model"}

    with pytest.raises(InvalidModelError):
        client.post("/transcribe", files=files, data=data)


def test_transcribe_audio_unsupported_format():
    """サポートされていないファイル形式のテスト"""
    import pytest
    from app.core.exceptions import UnsupportedAudioFormatError
    
    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.txt", io.BytesIO(fake_audio_data), "text/plain")}

    with pytest.raises(UnsupportedAudioFormatError):
        client.post("/transcribe", files=files)


def test_transcribe_audio_no_file():
    """ファイルなしの場合のテスト"""
    response = client.post("/transcribe")
    assert response.status_code == 422  # Validation error