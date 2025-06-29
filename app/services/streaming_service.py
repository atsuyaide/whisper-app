import tempfile
import wave
from typing import Dict, Any
import logging
from pathlib import Path
from .whisper_service import whisper_manager

logger = logging.getLogger(__name__)


class AudioBuffer:
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 2.0):
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.buffer: bytearray = bytearray()
        self.processed_chunks = 0
        self.detected_sample_rate: int | None = None

    def add_data(self, data: bytes) -> None:
        self.buffer.extend(data)

    def update_sample_rate(self, sample_rate: int) -> None:
        """実際の音声ファイルのサンプルレートに更新"""
        if self.detected_sample_rate != sample_rate:
            self.detected_sample_rate = sample_rate
            self.sample_rate = sample_rate
            self.chunk_size = int(sample_rate * self.chunk_duration)
            logger.info(
                f"Sample rate updated to {sample_rate} Hz, chunk_size: {self.chunk_size}"
            )

    def get_chunk_if_ready(self) -> bytes | None:
        if len(self.buffer) >= self.chunk_size * 2:  # 16-bit samples
            chunk_data = bytes(self.buffer[: self.chunk_size * 2])
            self.buffer = self.buffer[self.chunk_size * 2 :]
            return chunk_data
        return None

    def get_remaining_data(self) -> bytes:
        remaining = bytes(self.buffer)
        self.buffer.clear()
        return remaining


class StreamingTranscriptionService:
    def __init__(self, model_name: str = "base", language: str = "ja"):
        self.model_name = model_name
        self.language = language
        self.audio_buffer = AudioBuffer()
        self.accumulated_text = ""
        self.chunk_counter = 0

    async def process_audio_chunk(self, chunk_data: bytes) -> Dict[str, Any] | None:
        if len(chunk_data) < 1000:  # 最小チャンクサイズチェック
            return None

        try:
            # 一時WAVファイルを作成
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                # WAVヘッダーを作成
                with wave.open(temp_file.name, "wb") as wav_file:
                    wav_file.setnchannels(1)  # モノラル
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.audio_buffer.sample_rate)
                    wav_file.writeframes(chunk_data)

                # Whisperで文字起こし
                result = whisper_manager.transcribe(
                    temp_file.name, self.model_name, self.language
                )

                # 一時ファイルを削除
                Path(temp_file.name).unlink()

                self.chunk_counter += 1
                return {
                    "text": result["text"],
                    "start": self.chunk_counter * self.audio_buffer.chunk_duration,
                    "end": (self.chunk_counter + 1) * self.audio_buffer.chunk_duration,
                    "chunk_id": self.chunk_counter,
                }

        except Exception as e:
            logger.error(f"Chunk processing failed: {str(e)}")
            return None

    async def process_final_audio(self, remaining_data: bytes) -> Dict[str, Any]:
        if len(remaining_data) < 100:
            return {
                "text": self.accumulated_text,
                "language": "unknown",
                "segments": [],
                "model_used": self.model_name,
            }

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                with wave.open(temp_file.name, "wb") as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.audio_buffer.sample_rate)
                    wav_file.writeframes(remaining_data)

                result = whisper_manager.transcribe(
                    temp_file.name, self.model_name, self.language
                )
                Path(temp_file.name).unlink()

                return result

        except Exception as e:
            logger.error(f"Final processing failed: {str(e)}")
            return {
                "text": self.accumulated_text,
                "language": "unknown",
                "segments": [],
                "model_used": self.model_name,
            }

    def add_partial_text(self, text: str) -> None:
        if text.strip():
            self.accumulated_text += " " + text.strip()
