from typing import Annotated

from fastapi import Depends

from .config import settings
from .whisper_service import WhisperModelManager
from .streaming_service import StreamingTranscriptionService


class WhisperService:
    """Whisperサービスの統合インターフェース"""

    def __init__(self, model_manager: WhisperModelManager):
        self.model_manager = model_manager

    def get_available_models(self) -> list[str]:
        return self.model_manager.get_available_models()

    def is_valid_model(self, model_name: str) -> bool:
        return self.model_manager.is_valid_model(model_name)

    def get_model_status(self, model_name: str) -> dict:
        return self.model_manager.get_model_status(model_name)

    def load_model(self, model_name: str) -> object:
        return self.model_manager.load_model(model_name)

    def transcribe(
        self, audio_file_path: str, model_name: str, language: str | None = None
    ) -> dict:
        if language is None:
            language = settings.default_language
        return self.model_manager.transcribe(audio_file_path, model_name, language)

    def create_streaming_service(
        self, model_name: str, language: str | None = None
    ) -> StreamingTranscriptionService:
        if language is None:
            language = settings.default_language
        return StreamingTranscriptionService(model_name, language)


class ServiceContainer:
    """サービスコンテナ（シングルトン）"""

    _instance = None
    _whisper_manager = None

    def __new__(cls) -> "ServiceContainer":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def whisper_manager(self) -> WhisperModelManager:
        if self._whisper_manager is None:
            self._whisper_manager = WhisperModelManager()
        return self._whisper_manager


# DIコンテナインスタンス
_container = ServiceContainer()


def get_whisper_service() -> WhisperService:
    """WhisperServiceのDI用ファクトリ関数"""
    return WhisperService(_container.whisper_manager)


# 型ヒント付きDI
WhisperServiceDep = Annotated[WhisperService, Depends(get_whisper_service)]
