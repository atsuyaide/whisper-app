from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal


class TranscriptionRequest(BaseModel):
    model: str = Field(default="base", description="使用するWhisperモデル")


class TranscriptionSegment(BaseModel):
    text: str
    start: float
    end: float


class TranscriptionResult(BaseModel):
    text: str
    language: str
    segments: List[Dict[str, Any]]
    model_used: str


class TranscriptionResponse(BaseModel):
    filename: str
    content_type: str
    file_size: int
    transcription: TranscriptionResult
    status: str


class ModelsResponse(BaseModel):
    available_models: List[str]


class ModelStatusResponse(BaseModel):
    model: str
    is_ready: bool
    is_loaded: bool
    is_custom: bool
    message: str


class ModelInfoResponse(BaseModel):
    model: str
    exists: bool
    is_custom: bool = False
    is_loaded: bool = False
    type: str = "standard"
    file_path: str | None = None
    file_size: int | None = None
    last_modified: float | None = None
    message: str | None = None


class ModelLoadResponse(BaseModel):
    model: str
    is_loaded: bool
    load_time: float
    message: str


class HealthResponse(BaseModel):
    status: str


# WebSocketストリーミング用スキーマ
class StreamMessage(BaseModel):
    type: str


class ReadyMessage(StreamMessage):
    type: Literal["ready"] = "ready"


class PartialMessage(StreamMessage):
    type: Literal["partial"] = "partial"
    text: str
    start: float
    end: float
    chunk_id: int


class FinalMessage(StreamMessage):
    type: Literal["final"] = "final"
    text: str
    language: str
    segments: List[Dict[str, Any]]
    model_used: str


class ErrorMessage(StreamMessage):
    type: Literal["error"] = "error"
    message: str


class EndMessage(StreamMessage):
    type: Literal["end"] = "end"


class AudioInfoMessage(StreamMessage):
    type: Literal["audio_info"] = "audio_info"
    sample_rate: int
    channels: int
    sample_width: int
