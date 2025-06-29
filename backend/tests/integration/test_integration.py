import pytest
from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

client = TestClient(app)


class TestIntegration:
    @pytest.fixture
    def audio_files_dir(self):
        return Path(__file__).parent / "fixtures" / "audio"

    def test_transcribe_real_audio_wav(self, audio_files_dir):
        audio_file = audio_files_dir / "asano.wav"

        if not audio_file.exists():
            pytest.skip("Audio file asano.wav not found")

        with open(audio_file, "rb") as f:
            files = {"file": ("asano.wav", f, "audio/wav")}
            response = client.post("/transcribe", files=files)

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の確認
        assert data["filename"] == "asano.wav"
        assert data["content_type"] == "audio/wav"
        assert data["status"] == "success"
        assert "transcription" in data
        assert "text" in data["transcription"]
        assert "language" in data["transcription"]
        assert "segments" in data["transcription"]

        # 文字起こし結果が空でないことを確認
        assert len(data["transcription"]["text"].strip()) > 0

        print(f"Transcription result: {data['transcription']['text']}")
        print(f"Detected language: {data['transcription']['language']}")
        print(f"Model used: {data['transcription']['model_used']}")

    def test_transcribe_real_audio_mp3(self, audio_files_dir):
        audio_file = audio_files_dir / "asano.mp3"

        if not audio_file.exists():
            pytest.skip("Audio file asano.mp3 not found")

        with open(audio_file, "rb") as f:
            files = {"file": ("asano.mp3", f, "audio/mp3")}
            response = client.post("/transcribe", files=files)

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の確認
        assert data["filename"] == "asano.mp3"
        assert data["content_type"] == "audio/mp3"
        assert data["status"] == "success"
        assert "transcription" in data
        assert "text" in data["transcription"]
        assert "language" in data["transcription"]
        assert "segments" in data["transcription"]

        # 文字起こし結果が空でないことを確認
        assert len(data["transcription"]["text"].strip()) > 0

        print(f"Transcription result: {data['transcription']['text']}")
        print(f"Detected language: {data['transcription']['language']}")
        print(f"Model used: {data['transcription']['model_used']}")

    def test_transcribe_with_tiny_model(self, audio_files_dir):
        audio_file = audio_files_dir / "asano.wav"

        if not audio_file.exists():
            pytest.skip("Audio file asano.wav not found")

        with open(audio_file, "rb") as f:
            files = {"file": ("asano.wav", f, "audio/wav")}
            data = {"model": "tiny"}
            response = client.post("/transcribe", files=files, data=data)

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["transcription"]["model_used"] == "tiny"
        assert len(response_data["transcription"]["text"].strip()) > 0

        print(f"Tiny model result: {response_data['transcription']['text']}")

    def test_transcribe_file_size_check(self, audio_files_dir):
        audio_file = audio_files_dir / "asano.wav"

        if not audio_file.exists():
            pytest.skip("Audio file asano.wav not found")

        with open(audio_file, "rb") as f:
            file_content = f.read()
            files = {"file": ("asano.wav", file_content, "audio/wav")}
            response = client.post("/transcribe", files=files)

        data = response.json()
        assert data["file_size"] == len(file_content)
