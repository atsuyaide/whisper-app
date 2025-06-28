from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
import io

client = TestClient(app)


@patch("app.whisper_service.whisper_manager.transcribe")
def test_transcribe_audio_success(mock_transcribe):
    # モックの返り値を設定
    mock_transcribe.return_value = {
        "text": "Hello world",
        "language": "en",
        "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
        "model_used": "base",
    }

    # 仮の音声ファイルデータを作成
    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}

    response = client.post("/transcribe", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_audio.wav"
    assert data["content_type"] == "audio/wav"
    assert data["file_size"] == len(fake_audio_data)
    assert data["status"] == "success"
    assert data["transcription"]["text"] == "Hello world"
    assert data["transcription"]["language"] == "en"
    assert data["transcription"]["model_used"] == "base"


@patch("app.whisper_service.whisper_manager.transcribe")
def test_transcribe_audio_with_model_selection(mock_transcribe):
    # モックの返り値を設定
    mock_transcribe.return_value = {
        "text": "Hello world",
        "language": "en",
        "segments": [{"text": "Hello world", "start": 0.0, "end": 2.0}],
        "model_used": "tiny",
    }

    # 仮の音声ファイルデータを作成
    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}
    data = {"model": "tiny"}

    response = client.post("/transcribe", files=files, data=data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["transcription"]["model_used"] == "tiny"
    mock_transcribe.assert_called_with(mock_transcribe.call_args[0][0], "tiny")


def test_transcribe_audio_invalid_model():
    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.wav", io.BytesIO(fake_audio_data), "audio/wav")}
    data = {"model": "invalid_model"}

    response = client.post("/transcribe", files=files, data=data)

    assert response.status_code == 400
    assert "Invalid model" in response.json()["detail"]


def test_transcribe_audio_unsupported_format():
    fake_audio_data = b"fake audio content"
    files = {"file": ("test_audio.txt", io.BytesIO(fake_audio_data), "text/plain")}

    response = client.post("/transcribe", files=files)

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_transcribe_audio_no_file():
    response = client.post("/transcribe")

    assert response.status_code == 422  # Validation error
