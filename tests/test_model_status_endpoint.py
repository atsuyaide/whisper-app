#!/usr/bin/env python3
"""
モデル状態確認エンドポイントのテスト
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestModelStatusEndpoint:
    def test_model_status_valid_model(self):
        """有効なモデルの状態確認"""
        response = client.get("/models/base/status")
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "base"
        assert isinstance(data["is_ready"], bool)
        assert isinstance(data["is_loaded"], bool)
        assert "message" in data

    def test_model_status_invalid_model(self):
        """無効なモデルの状態確認"""
        response = client.get("/models/invalid_model/status")
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "invalid_model"
        assert data["is_ready"] is False
        assert data["is_loaded"] is False
        assert "Invalid model name" in data["message"]
        assert "Available models" in data["message"]

    def test_model_status_standard_models(self):
        """標準モデルの状態確認"""
        standard_models = ["tiny", "base", "small", "medium"]

        for model in standard_models:
            response = client.get(f"/models/{model}/status")
            assert response.status_code == 200

            data = response.json()
            assert data["model"] == model
            assert data["is_ready"] is True  # 標準モデルは常に利用可能

    def test_model_status_response_schema(self):
        """レスポンススキーマの確認"""
        response = client.get("/models/base/status")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["model", "is_ready", "is_loaded", "message"]

        for field in required_fields:
            assert field in data, f"Field '{field}' is missing from response"

        # 型チェック
        assert isinstance(data["model"], str)
        assert isinstance(data["is_ready"], bool)
        assert isinstance(data["is_loaded"], bool)
        assert isinstance(data["message"], str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
