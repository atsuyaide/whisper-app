import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel

# .envファイルを読み込み
load_dotenv()


class Settings(BaseModel):
    # アプリケーション設定
    app_name: str = os.getenv("APP_NAME", "Whisper音声文字起こしAPI")
    version: str = os.getenv("VERSION", "2.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # API設定
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "26214400"))  # デフォルト25MB
    allowed_audio_formats: List[str] = os.getenv(
        "ALLOWED_AUDIO_FORMATS", "audio/wav,audio/mp3,audio/mp4,audio/m4a,audio/flac"
    ).split(",")

    # Whisperモデル設定
    model_cache_dir: Path = Path(os.getenv("MODEL_CACHE_DIR", "models/whisper"))
    default_model: str = os.getenv("DEFAULT_MODEL", "base")
    available_models: List[str] = [
        "tiny",
        "base",
        "small",
        "medium",
        "large-v1",
        "large-v2",
        "large-v3",
    ]

    # ストリーミング設定
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "ja")
    chunk_duration: float = float(os.getenv("CHUNK_DURATION", "2.0"))
    default_sample_rate: int = int(os.getenv("DEFAULT_SAMPLE_RATE", "16000"))
    default_channels: int = 1
    default_sample_width: int = 2

    # サーバー設定
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # ログ設定
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
