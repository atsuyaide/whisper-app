import pytest
from unittest.mock import patch
from app.streaming_service import AudioBuffer, StreamingTranscriptionService


class TestAudioBufferUnit:
    def test_chunk_size_calculation(self):
        # 16kHz, 2秒 = 32000サンプル = 64000バイト（16-bit）
        buffer = AudioBuffer(sample_rate=16000, chunk_duration=2.0)
        assert buffer.chunk_size == 32000

        # 8kHz, 1秒 = 8000サンプル = 16000バイト（16-bit）
        buffer2 = AudioBuffer(sample_rate=8000, chunk_duration=1.0)
        assert buffer2.chunk_size == 8000

    def test_buffer_management(self):
        buffer = AudioBuffer(
            sample_rate=1000, chunk_duration=1.0
        )  # 2000バイトでチャンク

        # 段階的にデータを追加
        buffer.add_data(b"a" * 1000)
        assert buffer.get_chunk_if_ready() is None

        buffer.add_data(b"b" * 1200)
        chunk = buffer.get_chunk_if_ready()
        assert chunk is not None
        assert len(chunk) == 2000

        # 残りのデータが正しく保持されているか
        assert len(buffer.buffer) == 200

        # 残りを取得
        remaining = buffer.get_remaining_data()
        assert len(remaining) == 200
        assert len(buffer.buffer) == 0


class TestStreamingTranscriptionServiceUnit:
    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager")
    async def test_chunk_processing_workflow(self, mock_whisper_manager):
        mock_whisper_manager.transcribe.return_value = {
            "text": "Test transcription",
            "language": "en",
        }

        service = StreamingTranscriptionService(model_name="tiny", language="ja")

        # 十分なサイズのチャンクを作成
        chunk_data = b"x" * 5000

        result = await service.process_audio_chunk(chunk_data)

        assert result is not None
        assert result["text"] == "Test transcription"
        assert result["start"] == 2.0  # chunk_counter * chunk_duration
        assert result["end"] == 4.0
        assert result["chunk_id"] == 1

        # カウンターが増加しているか確認
        assert service.chunk_counter == 1

    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager")
    async def test_final_processing_with_accumulated_text(self, mock_whisper_manager):
        mock_whisper_manager.transcribe.return_value = {
            "text": "Final part",
            "language": "ja",
            "segments": [{"text": "Final part", "start": 0.0, "end": 1.0}],
            "model_used": "base",
        }

        service = StreamingTranscriptionService(language="ja")
        service.accumulated_text = " Previous chunks"

        result = await service.process_final_audio(b"x" * 1000)

        assert result["text"] == "Final part"
        assert result["language"] == "ja"
        assert result["model_used"] == "base"

    @pytest.mark.asyncio
    async def test_empty_final_processing(self):
        service = StreamingTranscriptionService(language="ja")
        service.accumulated_text = " Some previous text"

        # 極小データで最終処理
        result = await service.process_final_audio(b"x" * 50)

        assert result["text"] == " Some previous text"
        assert result["language"] == "unknown"
        assert result["segments"] == []

    def test_text_accumulation(self):
        service = StreamingTranscriptionService(language="ja")

        # 空文字列のテスト
        service.add_partial_text("")
        assert service.accumulated_text == ""

        # 空白のみのテスト
        service.add_partial_text("   ")
        assert service.accumulated_text == ""

        # 通常のテキスト
        service.add_partial_text("Hello")
        assert service.accumulated_text == " Hello"

        service.add_partial_text("world!")
        assert service.accumulated_text == " Hello world!"

        # 前後に空白があるテキスト
        service.add_partial_text("  extra  ")
        assert service.accumulated_text == " Hello world! extra"

    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager")
    async def test_error_handling_in_chunk_processing(self, mock_whisper_manager):
        mock_whisper_manager.transcribe.side_effect = Exception("Transcription failed")

        service = StreamingTranscriptionService(language="ja")
        chunk_data = b"x" * 5000

        result = await service.process_audio_chunk(chunk_data)

        # エラー時はNoneが返される
        assert result is None
        # カウンターは増加しない
        assert service.chunk_counter == 0

    @pytest.mark.asyncio
    @patch("app.streaming_service.whisper_manager")
    async def test_error_handling_in_final_processing(self, mock_whisper_manager):
        mock_whisper_manager.transcribe.side_effect = Exception(
            "Final transcription failed"
        )

        service = StreamingTranscriptionService(language="ja")
        service.accumulated_text = " Partial results"

        result = await service.process_final_audio(b"x" * 1000)

        # エラー時は蓄積されたテキストが返される
        assert result["text"] == " Partial results"
        assert result["language"] == "unknown"
        assert result["segments"] == []
