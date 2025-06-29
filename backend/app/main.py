import json
import logging
import time

from fastapi import (
    FastAPI,
    File,
    Form,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)

from .api.dependencies import WhisperServiceDep
from .core.config import settings
from .core.exceptions import (
    AudioProcessingError,
    FileTooLargeError,
    InvalidModelError,
    ModelLoadError,
    UnsupportedAudioFormatError,
)
from .schemas.schemas import (
    ErrorMessage,
    FinalMessage,
    HealthResponse,
    ModelInfoResponse,
    ModelLoadResponse,
    ModelsResponse,
    ModelStatusResponse,
    PartialMessage,
    ReadyMessage,
    TranscriptionResponse,
    TranscriptionResult,
)
from .utils.utils import AudioFileProcessor, validate_audio_format, validate_file_size

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="音声ファイルを文字起こしするAPI",
    version=settings.version,
    debug=settings.debug,
)



@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/models", response_model=ModelsResponse)
async def get_available_models(whisper_service: WhisperServiceDep) -> ModelsResponse:
    return ModelsResponse(available_models=whisper_service.get_available_models())


@app.get("/models/{model_name}/status", response_model=ModelStatusResponse)
async def get_model_status(
    model_name: str, whisper_service: WhisperServiceDep
) -> ModelStatusResponse:
    status = whisper_service.get_model_status(model_name)
    return ModelStatusResponse(**status)


@app.get("/models/{model_name}/info", response_model=ModelInfoResponse)
async def get_model_info(
    model_name: str, whisper_service: WhisperServiceDep
) -> ModelInfoResponse:
    """モデルの詳細情報を取得（カスタムモデルの場合はファイル情報も含む）"""
    info = whisper_service.model_manager.get_model_info(model_name)
    return ModelInfoResponse(**info)


@app.post("/models/{model_name}/load", response_model=ModelLoadResponse)
async def load_model(
    model_name: str, whisper_service: WhisperServiceDep
) -> ModelLoadResponse:
    """指定されたモデルを事前にロードする"""
    if not whisper_service.is_valid_model(model_name):
        raise InvalidModelError(model_name, whisper_service.get_available_models())

    status = whisper_service.get_model_status(model_name)
    if status["is_loaded"]:
        return ModelLoadResponse(
            model=model_name,
            is_loaded=True,
            load_time=0.0,
            message="Model was already loaded",
        )

    try:
        start_time = time.time()
        whisper_service.load_model(model_name)
        load_time = time.time() - start_time

        return ModelLoadResponse(
            model=model_name,
            is_loaded=True,
            load_time=load_time,
            message=f"Model loaded successfully in {load_time:.2f} seconds",
        )

    except Exception as e:
        raise ModelLoadError(model_name, str(e))


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    whisper_service: WhisperServiceDep,
    file: UploadFile = File(..., description="音声ファイル (WAV, MP3, MP4, M4A, FLAC)"),
    model: str = Form(settings.default_model, description="使用するWhisperモデル"),
    language: str = Form(settings.default_language, description="音声の言語コード"),
) -> TranscriptionResponse:
    file_content = await file.read()
    if not validate_file_size(len(file_content)):
        raise FileTooLargeError(len(file_content), settings.max_file_size)

    if file.content_type and not validate_audio_format(file.content_type):
        raise UnsupportedAudioFormatError(
            file.content_type, settings.allowed_audio_formats
        )

    if not whisper_service.is_valid_model(model):
        raise InvalidModelError(model, whisper_service.get_available_models())

    temp_file_path = None
    try:
        temp_file_path = AudioFileProcessor.save_uploaded_file(
            file_content, suffix=".tmp"
        )

        transcription_result = whisper_service.transcribe(
            str(temp_file_path), model, language
        )

        return TranscriptionResponse(
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            file_size=len(file_content),
            transcription=TranscriptionResult(**transcription_result),
            status="completed",
        )

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise AudioProcessingError("transcription", str(e))
    finally:
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()


@app.websocket("/stream-transcribe")
async def stream_transcribe(
    websocket: WebSocket,
    model: str = settings.default_model,
    language: str = settings.default_language,
) -> None:
    await websocket.accept()

    # WebSocketエンドポイントではFastAPIの依存性注入が使用できないため手動でサービスを取得
    from .api.dependencies import get_whisper_service

    whisper_service = get_whisper_service()

    if not whisper_service.is_valid_model(model):
        error_msg = ErrorMessage(
            message=f"Invalid model: {model}. Available models: {whisper_service.get_available_models()}"
        )
        await websocket.send_text(error_msg.model_dump_json())
        await websocket.close()
        return

    streaming_service = whisper_service.create_streaming_service(model, language)

    ready_msg = ReadyMessage()
    await websocket.send_text(ready_msg.model_dump_json())

    try:
        while True:
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if message["type"] == "websocket.receive" and "bytes" in message:
                audio_data = message["bytes"]
                streaming_service.audio_buffer.add_data(audio_data)

                chunk_data = streaming_service.audio_buffer.get_chunk_if_ready()
                if chunk_data:
                    partial_result = await streaming_service.process_audio_chunk(
                        chunk_data
                    )
                    if partial_result:
                        streaming_service.add_partial_text(partial_result["text"])
                        partial_msg = PartialMessage(**partial_result)
                        await websocket.send_text(partial_msg.model_dump_json())

            elif message["type"] == "websocket.receive" and "text" in message:
                try:
                    control_msg = json.loads(message["text"])
                    if control_msg.get("type") == "audio_info":
                        sample_rate = control_msg.get(
                            "sample_rate", settings.default_sample_rate
                        )
                        streaming_service.audio_buffer.update_sample_rate(sample_rate)
                        logger.info(f"Audio info received: {sample_rate}Hz")

                    elif control_msg.get("type") == "end":
                        remaining_data = (
                            streaming_service.audio_buffer.get_remaining_data()
                        )
                        final_result = await streaming_service.process_final_audio(
                            remaining_data
                        )

                        final_msg = FinalMessage(**final_result)
                        await websocket.send_text(final_msg.model_dump_json())
                        break

                except json.JSONDecodeError:
                    error_msg = ErrorMessage(message="Invalid JSON in control message")
                    await websocket.send_text(error_msg.model_dump_json())

    except WebSocketDisconnect:
        logger.info("WebSocket connection disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        error_msg = ErrorMessage(message=f"Server error: {str(e)}")
        try:
            await websocket.send_text(error_msg.model_dump_json())
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
