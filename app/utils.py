import tempfile
import wave
from pathlib import Path

from .config import settings
from .exceptions import AudioProcessingError


class AudioFileProcessor:
    """音声ファイル処理のユーティリティクラス"""

    @staticmethod
    def create_temp_wav(
        data: bytes,
        sample_rate: int,
        channels: int | None = None,
        sample_width: int | None = None,
    ) -> Path:
        """音声データから一時WAVファイルを作成"""
        if channels is None:
            channels = settings.default_channels
        if sample_width is None:
            sample_width = settings.default_sample_width

        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(temp_file.name, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(data)
            return Path(temp_file.name)
        except Exception as e:
            raise AudioProcessingError("create_temp_wav", str(e))

    @staticmethod
    def get_audio_info(file_path: Path) -> dict:
        """WAVファイルの音声情報を取得"""
        try:
            with wave.open(str(file_path), "rb") as wav_file:
                return {
                    "channels": wav_file.getnchannels(),
                    "sample_width": wav_file.getsampwidth(),
                    "sample_rate": wav_file.getframerate(),
                    "frames": wav_file.getnframes(),
                    "duration": wav_file.getnframes() / wav_file.getframerate(),
                }
        except Exception as e:
            raise AudioProcessingError("get_audio_info", str(e))

    @staticmethod
    def save_uploaded_file(file_content: bytes, suffix: str = ".tmp") -> Path:
        """アップロードされたファイルを一時保存"""
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
            temp_file.write(file_content)
            temp_file.close()
            return Path(temp_file.name)
        except Exception as e:
            raise AudioProcessingError("save_uploaded_file", str(e))


def validate_audio_format(content_type: str) -> bool:
    """音声フォーマットの妥当性チェック"""
    return content_type in settings.allowed_audio_formats


def validate_file_size(file_size: int) -> bool:
    """ファイルサイズの妥当性チェック"""
    return file_size <= settings.max_file_size
