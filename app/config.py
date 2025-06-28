from pathlib import Path
from typing import List

from pydantic import BaseModel


class Settings(BaseModel):
    # アプリケーション設定
    app_name: str = "Whisper音声文字起こしAPI"
    version: str = "2.0.0"
    debug: bool = False

    # API設定
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_audio_formats: List[str] = [
        "audio/wav",
        "audio/mpeg",
        "audio/mp4",
        "audio/x-m4a",
        "audio/flac",
        "audio/ogg",
        "audio/webm",
    ]

    # Whisperモデル設定
    model_cache_dir: Path = Path("models/whisper")
    default_model: str = "base"
    available_models: List[str] = ["tiny", "base", "small", "medium", "large"]

    # ストリーミング設定
    default_language: str = "ja"
    chunk_duration: float = 2.0
    default_sample_rate: int = 16000
    default_channels: int = 1
    default_sample_width: int = 2

    # ログ設定
    log_level: str = "INFO"


settings = Settings()
