from fastapi import Request
from fastapi.responses import JSONResponse

from .exceptions import (
    WhisperAppException,
    InvalidModelError,
    ModelLoadError,
    AudioProcessingError,
    UnsupportedAudioFormatError,
    FileTooLargeError,
)


async def whisper_app_exception_handler(
    request: Request, exc: WhisperAppException
) -> JSONResponse:
    """Whisperアプリケーション例外の共通ハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": exc.message,
            "details": exc.details,
        },
    )


async def invalid_model_error_handler(
    request: Request, exc: InvalidModelError
) -> JSONResponse:
    """無効なモデル名エラーハンドラー"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_model",
            "message": exc.message,
            "details": exc.details,
            "invalid_model": exc.model,
            "available_models": exc.available_models,
        },
    )


async def model_load_error_handler(
    request: Request, exc: ModelLoadError
) -> JSONResponse:
    """モデルロードエラーハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "model_load_failed",
            "message": exc.message,
            "details": exc.details,
            "model": exc.model,
        },
    )


async def audio_processing_error_handler(
    request: Request, exc: AudioProcessingError
) -> JSONResponse:
    """音声処理エラーハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "audio_processing_failed",
            "message": exc.message,
            "details": exc.details,
            "operation": exc.operation,
        },
    )


async def unsupported_audio_format_error_handler(
    request: Request, exc: UnsupportedAudioFormatError
) -> JSONResponse:
    """サポートされていない音声フォーマットエラーハンドラー"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "unsupported_audio_format",
            "message": exc.message,
            "details": exc.details,
            "content_type": exc.content_type,
            "supported_formats": exc.supported_formats,
        },
    )


async def file_too_large_error_handler(
    request: Request, exc: FileTooLargeError
) -> JSONResponse:
    """ファイルサイズ超過エラーハンドラー"""
    return JSONResponse(
        status_code=413,
        content={
            "error": "file_too_large",
            "message": exc.message,
            "details": exc.details,
            "file_size": exc.file_size,
            "max_size": exc.max_size,
        },
    )
