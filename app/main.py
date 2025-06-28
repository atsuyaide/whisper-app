from fastapi import FastAPI, File, UploadFile, HTTPException, Form
import tempfile
import os
from .schemas import TranscriptionResponse, ModelsResponse, HealthResponse

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


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="音声ファイル (WAV, MP3, MP4, M4A, FLAC)"),
    model: str = Form("base", description="使用するWhisperモデル"),
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
        transcription_result = whisper_manager.transcribe(temp_file_path, model)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
