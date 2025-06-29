from unittest.mock import patch, Mock
from app.services.whisper_service import WhisperModelManager, STANDARD_MODELS


class TestModelDiscovery:
    def test_scan_local_models_empty_directory(self):
        manager = WhisperModelManager()
        # モデルディレクトリが空の場合
        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = []

            local_models = manager._scan_local_models()
            assert local_models == []

    def test_scan_local_models_with_valid_files(self):
        manager = WhisperModelManager()

        # 有効なモデルファイルをモック
        mock_files = [
            Mock(stem="base"),
            Mock(stem="tiny"),
            Mock(stem="large-v3"),
            Mock(stem="custom-model"),  # 無効なファイル名
            Mock(stem="base-v1"),  # 無効なファイル名
        ]

        with patch("pathlib.Path.glob") as mock_glob:
            mock_glob.return_value = mock_files

            local_models = manager._scan_local_models()

            # 有効なモデル名のみが返される
            assert "base" in local_models
            assert "tiny" in local_models
            assert "large-v3" in local_models
            assert "custom-model" not in local_models
            assert "base-v1" not in local_models

    def test_get_available_models_standard_only(self):
        manager = WhisperModelManager()

        # ローカルモデルがない場合
        with patch.object(manager, "_scan_local_models") as mock_scan:
            mock_scan.return_value = []

            models = manager.get_available_models()

            # 標準モデルのみが返される
            assert set(models) == set(STANDARD_MODELS)
            assert models == sorted(STANDARD_MODELS)

    def test_get_available_models_with_local_models(self):
        manager = WhisperModelManager()

        # ローカルに追加のモデルがある場合
        local_models = ["tiny", "medium"]  # tinyは重複

        with patch.object(manager, "_scan_local_models") as mock_scan:
            mock_scan.return_value = local_models

            models = manager.get_available_models()

            # 重複なしでソートされている
            expected_models = sorted(set(STANDARD_MODELS + local_models))
            assert models == expected_models

    def test_get_available_models_with_new_local_models(self):
        manager = WhisperModelManager()

        # ローカルに新しいモデルがある場合（実際には標準モデル名のみ有効）
        local_models = ["base", "small"]  # 既存モデル

        with patch.object(manager, "_scan_local_models") as mock_scan:
            mock_scan.return_value = local_models

            models = manager.get_available_models()

            # 標準モデルと同じ
            assert set(models) == set(STANDARD_MODELS)

    def test_is_valid_model_with_dynamic_models(self):
        manager = WhisperModelManager()

        # ローカルモデルを含む場合
        with patch.object(manager, "get_available_models") as mock_get_models:
            mock_get_models.return_value = ["tiny", "base", "custom"]

            assert manager.is_valid_model("tiny") is True
            assert manager.is_valid_model("base") is True
            assert manager.is_valid_model("custom") is True
            assert manager.is_valid_model("invalid") is False

    def test_model_directory_creation(self):
        # 新しいマネージャーインスタンスでディレクトリが作成されることを確認
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            WhisperModelManager()

            # mkdir が parents=True, exist_ok=True で呼ばれることを確認
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)
