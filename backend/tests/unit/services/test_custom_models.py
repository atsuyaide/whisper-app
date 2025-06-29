from unittest.mock import patch
from app.services.whisper_service import WhisperModelManager


class TestCustomModelSupport:
    def test_scan_custom_models(self, tmp_path):
        """カスタムモデルのスキャン機能テスト"""
        # テスト用のモデルディレクトリ作成
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)

        # テスト用のカスタムモデルファイル作成
        (model_dir / "tiny-fine-tuned.pt").write_text("dummy model")
        (model_dir / "custom-model-v1.pt").write_text("dummy model")
        (model_dir / "invalid-name!.pt").write_text("invalid")  # 無効な文字

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        local_models = manager._scan_local_models()

        # 有効なカスタムモデルのみが検出される
        assert "tiny-fine-tuned" in local_models
        assert "custom-model-v1" in local_models
        assert "invalid-name!" not in local_models  # 無効な文字は除外

    def test_is_custom_model(self, tmp_path):
        """カスタムモデル判定テスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        (model_dir / "custom-model.pt").write_text("dummy")

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # カスタムモデル
        assert manager.is_custom_model("custom-model") is True

        # 標準モデル
        assert manager.is_custom_model("base") is False
        assert manager.is_custom_model("tiny") is False

        # 存在しないモデル
        assert manager.is_custom_model("nonexistent") is False

    def test_get_model_path(self, tmp_path):
        """モデルパス取得テスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        custom_file = model_dir / "custom-model.pt"
        custom_file.write_text("dummy")

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # カスタムモデルのパス
        path = manager.get_model_path("custom-model")
        assert path == str(custom_file)

        # 標準モデルのパス（モデル名をそのまま返す）
        path = manager.get_model_path("base")
        assert path == "base"

        # 存在しないモデル
        path = manager.get_model_path("nonexistent")
        assert path is None

    def test_get_model_info(self, tmp_path):
        """モデル情報取得テスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        custom_file = model_dir / "custom-model.pt"
        custom_file.write_text("dummy model content")

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # カスタムモデルの情報
        info = manager.get_model_info("custom-model")
        assert info["model"] == "custom-model"
        assert info["exists"] is True
        assert info["is_custom"] is True
        assert info["type"] == "custom"
        assert info["file_path"] == str(custom_file)
        assert info["file_size"] > 0

        # 標準モデルの情報
        info = manager.get_model_info("base")
        assert info["model"] == "base"
        assert info["exists"] is True
        assert info["is_custom"] is False
        assert info["type"] == "standard"
        assert info["file_path"] is None

        # 存在しないモデル
        info = manager.get_model_info("nonexistent")
        assert info["exists"] is False

    def test_get_available_models_with_custom(self, tmp_path):
        """カスタムモデル込みの利用可能モデル一覧テスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        (model_dir / "custom-1.pt").write_text("dummy")
        (model_dir / "custom-2.pt").write_text("dummy")

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        models = manager.get_available_models()

        # 標準モデルが含まれている
        assert "tiny" in models
        assert "base" in models

        # カスタムモデルが含まれている
        assert "custom-1" in models
        assert "custom-2" in models

        # ソートされている
        assert models == sorted(models)

    @patch("app.services.whisper_service.whisper.load_model")
    def test_load_custom_model(self, mock_load_model, tmp_path):
        """カスタムモデルロードテスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        custom_file = model_dir / "custom-model.pt"
        custom_file.write_text("dummy model")

        mock_model = object()
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # カスタムモデルのロード
        result = manager.load_model("custom-model")

        assert result == mock_model
        assert "custom-model" in manager.loaded_models

        # whisper.load_modelが正しいパスで呼ばれた
        mock_load_model.assert_called_once_with(str(custom_file))

    @patch("app.services.whisper_service.whisper.load_model")
    def test_load_standard_model_with_custom_support(self, mock_load_model, tmp_path):
        """標準モデルロード（カスタムモデル機能付き）テスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)

        mock_model = object()
        mock_load_model.return_value = mock_model

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # 標準モデルのロード
        result = manager.load_model("base")

        assert result == mock_model
        assert "base" in manager.loaded_models

        # 標準モデルはモデル名で呼ばれる
        mock_load_model.assert_called_once_with("base", download_root=str(model_dir))

    def test_model_status_with_custom_flag(self, tmp_path):
        """カスタムモデルフラグ付きステータステスト"""
        model_dir = tmp_path / "models" / "whisper"
        model_dir.mkdir(parents=True)
        (model_dir / "custom-model.pt").write_text("dummy")

        manager = WhisperModelManager()
        manager.model_dir = model_dir

        # カスタムモデルのステータス
        status = manager.get_model_status("custom-model")
        assert status["is_custom"] is True
        assert "Custom" in status["message"]

        # 標準モデルのステータス
        status = manager.get_model_status("base")
        assert status["is_custom"] is False
        assert "Standard" in status["message"]
