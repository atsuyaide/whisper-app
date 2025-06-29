#!/usr/bin/env python3
"""
モデル状態確認エンドポイントのテスト
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestModelStatusEndpoint:
    def test_model_status_valid_model(self, override_whisper_service):
        """有効なモデルの状態確認"""
        mock_service = override_whisper_service
        mock_service.get_model_status.return_value = {
            "model": "base",
            "is_ready": True,
            "is_loaded": False,
            "is_custom": False,
            "message": "Model is available but not loaded yet",
        }

        response = client.get("/models/base/status")
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "base"
        assert isinstance(data["is_ready"], bool)
        assert isinstance(data["is_loaded"], bool)
        assert "message" in data

    def test_model_status_invalid_model(self, override_whisper_service):
        """無効なモデルの状態確認"""
        mock_service = override_whisper_service
        mock_service.get_model_status.return_value = {
            "model": "invalid_model",
            "is_ready": False,
            "is_loaded": False,
            "is_custom": False,
            "message": "Invalid model name. Available models: ['tiny', 'base', 'small']",
        }

        response = client.get("/models/invalid_model/status")
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "invalid_model"
        assert data["is_ready"] is False
        assert data["is_loaded"] is False

    def test_model_status_response_schema(self, override_whisper_service):
        """レスポンススキーマの確認"""
        mock_service = override_whisper_service
        mock_service.get_model_status.return_value = {
            "model": "base",
            "is_ready": True,
            "is_loaded": False,
            "is_custom": False,
            "message": "Model is available but not loaded yet",
        }

        response = client.get("/models/base/status")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["model", "is_ready", "is_loaded", "message"]
        for field in required_fields:
            assert field in data

    def test_model_status_standard_models(self, override_whisper_service):
        """標準モデルの状態確認"""
        mock_service = override_whisper_service
        
        standard_models = ["tiny", "base", "small", "medium", "large"]
        for model in standard_models:
            mock_service.get_model_status.return_value = {
                "model": model,
                "is_ready": True,
                "is_loaded": False,
                "is_custom": False,
                "message": f"Standard model {model} is available but not loaded yet",
            }

            response = client.get(f"/models/{model}/status")
            assert response.status_code == 200

            data = response.json()
            assert data["model"] == model
            assert isinstance(data["is_ready"], bool)
            assert isinstance(data["is_loaded"], bool)