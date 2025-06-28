from pydantic import BaseModel, Field
from typing import List, Dict, Any


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


class HealthResponse(BaseModel):
    status: str
