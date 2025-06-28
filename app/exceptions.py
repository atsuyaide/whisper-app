from typing import List, Optional


class WhisperAppException(Exception):
    """Whisperアプリケーションのベース例外"""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)


class InvalidModelError(WhisperAppException):
    """無効なモデル名エラー"""

    def __init__(self, model: str, available_models: List[str]):
        self.model = model
        self.available_models = available_models
        message = f"Invalid model: {model}"
        details = f"Available models: {', '.join(available_models)}"
        super().__init__(message, details)


class ModelLoadError(WhisperAppException):
    """モデルロードエラー"""

    def __init__(self, model: str, error_message: str):
        self.model = model
        self.error_message = error_message
        message = f"Failed to load model '{model}'"
        super().__init__(message, error_message)


class AudioProcessingError(WhisperAppException):
    """音声処理エラー"""

    def __init__(self, operation: str, error_message: str):
        self.operation = operation
        self.error_message = error_message
        message = f"Audio processing failed during {operation}"
        super().__init__(message, error_message)


class UnsupportedAudioFormatError(WhisperAppException):
    """サポートされていない音声フォーマットエラー"""

    def __init__(self, content_type: str, supported_formats: List[str]):
        self.content_type = content_type
        self.supported_formats = supported_formats
        message = f"Unsupported audio format: {content_type}"
        details = f"Supported formats: {', '.join(supported_formats)}"
        super().__init__(message, details)


class FileTooLargeError(WhisperAppException):
    """ファイルサイズ超過エラー"""

    def __init__(self, file_size: int, max_size: int):
        self.file_size = file_size
        self.max_size = max_size
        message = f"File too large: {file_size} bytes"
        details = f"Maximum allowed size: {max_size} bytes"
        super().__init__(message, details)
