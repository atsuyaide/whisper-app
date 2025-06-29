#!/usr/bin/env python3
"""
streaming.pyのテストファイル
"""

import pytest
import tempfile
import wave
import math
import struct
from pathlib import Path
from unittest.mock import patch, AsyncMock
import json

from streaming import read_audio_file, stream_transcription, check_model_status


class TestStreamingDemo:
    def create_test_wav(self, duration: float = 2.0, sample_rate: int = 16000) -> Path:
        """テスト用のWAVファイルを作成"""
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(temp_file.name)
        temp_file.close()

        frames = int(sample_rate * duration)

        with wave.open(str(temp_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # モノラル
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            # サイン波を生成（440Hz A音）
            audio_data = []
            for i in range(frames):
                value = int(32767 * 0.3 * math.sin(2 * math.pi * 440 * i / sample_rate))
                audio_data.append(struct.pack("<h", value))

            wav_file.writeframes(b"".join(audio_data))

        return temp_path

    @pytest.mark.asyncio
    async def test_read_audio_file_success(self):
        """音声ファイル読み込みの正常ケース"""
        test_wav = self.create_test_wav(duration=1.0)

        try:
            chunks = []
            async for chunk in read_audio_file(test_wav, chunk_size=8192):
                chunks.append(chunk)

            # チャンクが取得できることを確認
            assert len(chunks) > 0
            # 各チャンクがbytesであることを確認
            for chunk in chunks:
                assert isinstance(chunk, bytes)
                assert len(chunk) > 0

        finally:
            test_wav.unlink()

    @pytest.mark.asyncio
    async def test_read_audio_file_not_found(self):
        """存在しないファイルの場合"""
        non_existent_file = Path("non_existent.wav")

        with pytest.raises(FileNotFoundError):
            async for chunk in read_audio_file(non_existent_file):
                pass

    @pytest.mark.asyncio
    async def test_read_audio_file_invalid_wav(self):
        """不正なWAVファイルの場合"""
        # テキストファイルを作成
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(temp_file.name)

        with open(temp_path, "w") as f:
            f.write("This is not a WAV file")

        try:
            with pytest.raises(wave.Error):
                async for chunk in read_audio_file(temp_path):
                    pass
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    @patch("websockets.connect")
    async def test_stream_transcription_success(self, mock_connect):
        """WebSocketストリーミングの正常ケース"""
        test_wav = self.create_test_wav(duration=0.5)

        # WebSocketの模擬オブジェクト
        mock_websocket = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_websocket

        # 受信メッセージの設定
        messages = [
            json.dumps({"type": "ready"}),
            json.dumps({"type": "partial", "text": "Hello", "chunk_id": 1}),
            json.dumps(
                {
                    "type": "final",
                    "text": "Hello world",
                    "language": "en",
                    "model_used": "base",
                }
            ),
        ]
        mock_websocket.recv.side_effect = messages

        # モデル状態確認をモック
        with patch("streaming.check_model_status") as mock_check_status:
            mock_check_status.return_value = {
                "model": "tiny",
                "is_ready": True,
                "is_loaded": True,
                "message": "Model is loaded and ready",
            }

            try:
                # stream_transcriptionを実行
                await stream_transcription(
                    test_wav,
                    host="localhost",
                    port=8000,
                    model="tiny",
                    language="en",
                    play_audio=False,
                )

                # WebSocketに接続されたことを確認
                mock_connect.assert_called_once_with(
                    "ws://localhost:8000/stream-transcribe?model=tiny&language=en"
                )

                # メッセージが送信されたことを確認
                assert mock_websocket.send.call_count >= 2

            finally:
                test_wav.unlink()

    @pytest.mark.asyncio
    @patch("websockets.connect")
    async def test_stream_transcription_connection_error(self, mock_connect):
        """接続エラーのテストケース"""

        test_wav = self.create_test_wav(duration=0.1)
        mock_connect.side_effect = ConnectionRefusedError()

        with patch("streaming.check_model_status") as mock_check_status:
            mock_check_status.return_value = {
                "model": "base",
                "is_ready": False,
                "is_loaded": False,
                "message": "Cannot connect to API server at localhost:9999",
            }

            try:
                # 例外が発生せず正常終了することを確認
                await stream_transcription(
                    test_wav, host="localhost", port=9999, play_audio=False
                )
            finally:
                test_wav.unlink()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_model_status_success(self, mock_client_class):
        """モデル状態確認の正常ケース"""
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.json.return_value = {
            "model": "base",
            "is_ready": True,
            "is_loaded": True,
            "message": "Model is loaded and ready",
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await check_model_status("localhost", 8000, "base")

        assert result["model"] == "base"
        assert result["is_ready"] is True
        assert result["is_loaded"] is True
        mock_client.get.assert_called_once_with(
            "http://localhost:8000/models/base/status"
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_model_status_connection_error(self, mock_client_class):
        """モデル状態確認の接続エラーケース"""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        import httpx

        mock_client.get.side_effect = httpx.ConnectError("Connection failed")

        result = await check_model_status("localhost", 9999, "base")

        assert result["model"] == "base"
        assert result["is_ready"] is False
        assert result["is_loaded"] is False
        assert "Cannot connect to API server" in result["message"]


def test_import():
    """モジュールが正常にインポートできることを確認"""
    import streaming

    assert hasattr(streaming, "read_audio_file")
    assert hasattr(streaming, "stream_transcription")
    assert hasattr(streaming, "main")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
