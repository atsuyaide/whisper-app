from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Form,
    WebSocket,
    WebSocketDisconnect,
)
import tempfile
import os
import json
import logging
from .schemas import (
    TranscriptionResponse,
    ModelsResponse,
    HealthResponse,
    ModelStatusResponse,
    ModelLoadResponse,
    ReadyMessage,
    PartialMessage,
    FinalMessage,
    ErrorMessage,
)
from .streaming_service import StreamingTranscriptionService

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Whisper Transcription API",
    description="音声ファイルを文字起こしするAPI",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.get("/models", response_model=ModelsResponse)
async def get_available_models() -> ModelsResponse:
    from .whisper_service import whisper_manager

    return ModelsResponse(available_models=whisper_manager.get_available_models())


@app.get("/models/{model_name}/status", response_model=ModelStatusResponse)
async def get_model_status(model_name: str) -> ModelStatusResponse:
    from .whisper_service import whisper_manager

    status = whisper_manager.get_model_status(model_name)
    return ModelStatusResponse(**status)


@app.post("/models/{model_name}/load", response_model=ModelLoadResponse)
async def load_model(model_name: str) -> ModelLoadResponse:
    """指定されたモデルを事前にロードする"""
    from .whisper_service import whisper_manager
    import time

    if not whisper_manager.is_valid_model(model_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name: {model_name}. Available models: {whisper_manager.get_available_models()}",
        )

    # 既にロード済みかチェック
    if model_name in whisper_manager.loaded_models:
        return ModelLoadResponse(
            model=model_name,
            is_loaded=True,
            load_time=0.0,
            message="Model was already loaded",
        )

    try:
        start_time = time.time()
        whisper_manager.load_model(model_name)
        load_time = time.time() - start_time

        return ModelLoadResponse(
            model=model_name,
            is_loaded=True,
            load_time=load_time,
            message=f"Model loaded successfully in {load_time:.2f} seconds",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load model {model_name}: {str(e)}"
        )


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="音声ファイル (WAV, MP3, MP4, M4A, FLAC)"),
    model: str = Form("base", description="使用するWhisperモデル"),
    language: str = Form("ja", description="音声の言語コード"),
) -> TranscriptionResponse:
    # 対応する音声ファイル形式をチェック
    supported_formats = [
        "audio/wav",
        "audio/mp3",
        "audio/mpeg",
        "audio/mp4",
        "audio/m4a",
        "audio/flac",
    ]
    if file.content_type not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}",
        )

    # ファイルサイズチェック（100MB制限）
    max_size = 100 * 1024 * 1024  # 100MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 100MB"
        )

    # 一時ファイルに保存
    filename = file.filename or "audio"
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=os.path.splitext(filename)[1]
    ) as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name

    try:
        # モデル選択のバリデーション
        from .whisper_service import whisper_manager

        if not whisper_manager.is_valid_model(model):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {model}. Available models: {whisper_manager.get_available_models()}",
            )

        # Whisperを使った文字起こし処理
        transcription_result = whisper_manager.transcribe(
            temp_file_path, model, language
        )

        from .schemas import TranscriptionResult

        return TranscriptionResponse(
            filename=filename,
            content_type=file.content_type or "application/octet-stream",
            file_size=len(file_content),
            transcription=TranscriptionResult(**transcription_result),
            status="success",
        )

    finally:
        # 一時ファイルを削除
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@app.websocket("/stream-transcribe")
async def stream_transcribe(
    websocket: WebSocket, model: str = "base", language: str = "ja"
) -> None:
    await websocket.accept()

    # モデルの妥当性チェック
    from .whisper_service import whisper_manager

    if not whisper_manager.is_valid_model(model):
        error_msg = ErrorMessage(message=f"Invalid model: {model}")
        await websocket.send_text(error_msg.model_dump_json())
        await websocket.close()
        return

    # ストリーミングサービスを初期化
    streaming_service = StreamingTranscriptionService(
        model_name=model, language=language
    )

    # 準備完了メッセージを送信
    ready_msg = ReadyMessage()
    await websocket.send_text(ready_msg.model_dump_json())

    try:
        while True:
            # メッセージを受信
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            # バイナリデータ（音声チャンク）の場合
            if message["type"] == "websocket.receive" and "bytes" in message:
                audio_data = message["bytes"]
                streaming_service.audio_buffer.add_data(audio_data)

                # チャンクが準備できたら処理
                chunk_data = streaming_service.audio_buffer.get_chunk_if_ready()
                if chunk_data:
                    partial_result = await streaming_service.process_audio_chunk(
                        chunk_data
                    )
                    if partial_result:
                        streaming_service.add_partial_text(partial_result["text"])
                        partial_msg = PartialMessage(**partial_result)
                        await websocket.send_text(partial_msg.model_dump_json())

            # テキストメッセージ（コントロール）の場合
            elif message["type"] == "websocket.receive" and "text" in message:
                try:
                    control_msg = json.loads(message["text"])
                    if control_msg.get("type") == "audio_info":
                        # 音声情報を受信してAudioBufferを更新
                        sample_rate = control_msg.get("sample_rate", 16000)
                        streaming_service.audio_buffer.update_sample_rate(sample_rate)
                        logger.info(f"Audio info received: {sample_rate}Hz")

                    elif control_msg.get("type") == "end":
                        # 残りの音声データを処理
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
