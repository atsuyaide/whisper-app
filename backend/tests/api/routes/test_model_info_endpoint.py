#!/usr/bin/env python3
"""
モデル情報エンドポイントのテスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)


def test_get_model_info_standard_model(override_whisper_service):
    """標準モデルの情報取得テスト"""
    mock_service = override_whisper_service
    mock_service.model_manager.get_model_info.return_value = {
        "model": "base",
        "exists": True,
        "is_custom": False,
        "is_loaded": False,
        "type": "standard",
        "file_path": None,
        "file_size": None,
        "last_modified": None,
    }

    response = client.get("/models/base/info")
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "base"
    assert data["exists"] is True
    assert data["is_custom"] is False
    assert data["type"] == "standard"


def test_get_model_info_custom_model(override_whisper_service):
    """カスタムモデルの情報取得テスト"""
    mock_service = override_whisper_service
    mock_service.model_manager.get_model_info.return_value = {
        "model": "custom-model",
        "exists": True,
        "is_custom": True,
        "is_loaded": False,
        "type": "custom",
        "file_path": "/path/to/custom-model.pt",
        "file_size": 1024000,
        "last_modified": 1640995200,
    }

    response = client.get("/models/custom-model/info")
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "custom-model"
    assert data["exists"] is True
    assert data["is_custom"] is True
    assert data["type"] == "custom"
    assert data["file_path"] is not None
    assert data["file_size"] is not None


def test_get_model_info_nonexistent_model(override_whisper_service):
    """存在しないモデルの情報取得テスト"""
    mock_service = override_whisper_service
    mock_service.model_manager.get_model_info.return_value = {
        "model": "nonexistent",
        "exists": False,
        "message": "Model not found. Available models: ['tiny', 'base', 'small']",
    }

    response = client.get("/models/nonexistent/info")
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "nonexistent"
    assert data["exists"] is False
    assert "message" in data


def test_models_list_includes_custom_models(override_whisper_service):
    """モデル一覧にカスタムモデルが含まれることの確認"""
    mock_service = override_whisper_service
    mock_service.get_available_models.return_value = [
        "tiny", "base", "small", "medium", "large", "custom-model"
    ]

    response = client.get("/models")
    assert response.status_code == 200

    data = response.json()
    assert "custom-model" in data["available_models"]
    assert len(data["available_models"]) == 6


def test_model_status_with_custom_flag(override_whisper_service):
    """カスタムフラグ付きモデル状態確認"""
    mock_service = override_whisper_service
    mock_service.get_model_status.return_value = {
        "model": "custom-model",
        "is_ready": True,
        "is_loaded": False,
        "is_custom": True,
        "message": "Custom model is available but not loaded yet",
    }

    response = client.get("/models/custom-model/status")
    assert response.status_code == 200

    data = response.json()
    assert data["model"] == "custom-model"
    assert data["is_custom"] is True