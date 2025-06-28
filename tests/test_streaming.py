import pytest
import json
import wave
import tempfile
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.streaming_service import AudioBuffer, StreamingTranscriptionService

client = TestClient(app)


class TestAudioBuffer:
    def test_init(self):
        buffer = AudioBuffer(sample_rate=16000, chunk_duration=2.0)
        assert buffer.sample_rate == 16000
        assert buffer.chunk_duration == 2.0
        assert buffer.chunk_size == 32000
        assert len(buffer.buffer) == 0
        assert buffer.processed_chunks == 0

    def test_add_data(self):
        buffer = AudioBuffer()
        data = b"test audio data"
        buffer.add_data(data)
        assert len(buffer.buffer) == len(data)

    def test_get_chunk_if_ready(self):
        buffer = AudioBuffer(
            sample_rate=1000, chunk_duration=1.0
        )  # 2000 bytes for chunk

        # 不十分なデータ
        buffer.add_data(b"x" * 1000)
        assert buffer.get_chunk_if_ready() is None

        # 十分なデータ
        buffer.add_data(b"y" * 1500)
        chunk = buffer.get_chunk_if_ready()
        assert chunk is not None
        assert len(chunk) == 2000

    def test_get_remaining_data(self):
        buffer = AudioBuffer()
        test_data = b"remaining audio data"
        buffer.add_data(test_data)

        remaining = buffer.get_remaining_data()
        assert remaining == test_data
        assert len(buffer.buffer) == 0


class TestStreamingTranscriptionService:
    def test_init(self):
        service = StreamingTranscriptionService(model_name="tiny", language="ja")
        assert service.model_name == "tiny"
        assert service.accumulated_text == ""
        assert service.chunk_counter == 0

    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager.transcribe")
    async def test_process_audio_chunk_success(self, mock_transcribe):
        mock_transcribe.return_value = {"text": "Hello world", "language": "en"}

        service = StreamingTranscriptionService(language="ja")

        # 16-bit PCMデータを模擬（2秒分）
        chunk_data = b"x" * (16000 * 2 * 2)  # sample_rate * duration * bytes_per_sample

        result = await service.process_audio_chunk(chunk_data)

        assert result is not None
        assert result["text"] == "Hello world"
        assert result["chunk_id"] == 1
        assert service.chunk_counter == 1

    @pytest.mark.asyncio
    async def test_process_audio_chunk_too_small(self):
        service = StreamingTranscriptionService(language="ja")

        # 小さすぎるチャンク
        small_chunk = b"x" * 500

        result = await service.process_audio_chunk(small_chunk)
        assert result is None

    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager.transcribe")
    async def test_process_final_audio(self, mock_transcribe):
        mock_transcribe.return_value = {
            "text": "Final transcription",
            "language": "en",
            "segments": [],
            "model_used": "base",
        }

        service = StreamingTranscriptionService(language="ja")
        service.accumulated_text = "Previous text"

        final_data = b"x" * 1000
        result = await service.process_final_audio(final_data)

        assert result["text"] == "Final transcription"
        assert result["language"] == "en"

    def test_add_partial_text(self):
        service = StreamingTranscriptionService(language="ja")

        service.add_partial_text("Hello")
        assert service.accumulated_text == " Hello"

        service.add_partial_text("world")
        assert service.accumulated_text == " Hello world"


class TestWebSocketEndpoint:
    def create_test_wav_data(self, duration: float = 2.0) -> bytes:
        """テスト用のWAVデータを作成"""
        sample_rate = 16000
        frames = int(sample_rate * duration)

        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            with wave.open(temp_file.name, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                # サイン波を生成
                import struct
                import math

                audio_data = []
                for i in range(frames):
                    value = int(32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
                    audio_data.append(struct.pack("<h", value))
                wav_file.writeframes(b"".join(audio_data))

            with open(temp_file.name, "rb") as f:
                # WAVヘッダーをスキップして生のPCMデータを取得
                f.seek(44)  # WAVヘッダーは通常44バイト
                return f.read()

    @patch("app.streaming_service.whisper_manager.transcribe")
    def test_websocket_streaming_flow(self, mock_transcribe):
        mock_transcribe.side_effect = [
            {"text": "Hello", "language": "en"},
            {"text": "world", "language": "en", "segments": [], "model_used": "base"},
            {
                "text": "Hello world",
                "language": "en",
                "segments": [],
                "model_used": "base",
            },
        ]

        with client.websocket_connect("/stream-transcribe?model=base") as websocket:
            # 準備完了メッセージを受信
            ready_data = websocket.receive_text()
            ready_msg = json.loads(ready_data)
            assert ready_msg["type"] == "ready"

            # 音声チャンクを送信
            chunk1 = self.create_test_wav_data(2.1)  # チャンクサイズを超える
            websocket.send_bytes(chunk1)

            # 部分結果を受信
            partial_data = websocket.receive_text()
            partial_msg = json.loads(partial_data)
            assert partial_msg["type"] == "partial"
            assert "text" in partial_msg

            # 終了メッセージを送信
            end_msg = {"type": "end"}
            websocket.send_text(json.dumps(end_msg))

            # 最終結果を受信
            final_data = websocket.receive_text()
            final_msg = json.loads(final_data)
            assert final_msg["type"] == "final"
            assert "text" in final_msg

    def test_websocket_invalid_model(self):
        with client.websocket_connect("/stream-transcribe?model=invalid") as websocket:
            # エラーメッセージを受信
            error_data = websocket.receive_text()
            error_msg = json.loads(error_data)
            assert error_msg["type"] == "error"
            assert "Invalid model" in error_msg["message"]

    @patch("app.streaming_service.whisper_manager.transcribe")
    def test_websocket_invalid_json(self, mock_transcribe):
        with client.websocket_connect("/stream-transcribe?model=base") as websocket:
            # 準備完了メッセージを受信
            ready_data = websocket.receive_text()
            ready_msg = json.loads(ready_data)
            assert ready_msg["type"] == "ready"

            # 無効なJSONを送信
            websocket.send_text("invalid json")

            # エラーメッセージを受信
            error_data = websocket.receive_text()
            error_msg = json.loads(error_data)
            assert error_msg["type"] == "error"
            assert "Invalid JSON" in error_msg["message"]
