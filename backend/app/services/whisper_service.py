import whisper  # type: ignore
from typing import Dict, Any, List
import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# 標準のWhisperモデル
STANDARD_MODELS = [
    "tiny",
    "base",
    "small",
    "medium",
    "large-v1",
    "large-v2",
    "large-v3",
]

# モデル保存ディレクトリ
MODEL_DIR = Path("models/whisper")


class WhisperModelManager:
    def __init__(self) -> None:
        self.loaded_models: Dict[str, Any] = {}
        self.model_dir = MODEL_DIR
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _scan_local_models(self) -> List[str]:
        """ローカルに保存されたモデルファイルをスキャン（標準モデル + カスタムモデル）"""
        local_models = []
        if self.model_dir.exists():
            # .ptファイルを探す
            for model_file in self.model_dir.glob("*.pt"):
                model_name = model_file.stem
                # すべての.ptファイルを有効なモデルとして認識
                # ファイル名は英数字、ハイフン、アンダースコアのみ許可
                if re.match(r"^[a-zA-Z0-9_-]+$", model_name):
                    local_models.append(model_name)
                else:
                    logger.warning(f"Invalid model filename ignored: {model_file.name}")
        return local_models

    def get_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得（標準モデル + カスタムモデル）"""
        # 標準モデルから開始
        available_models = STANDARD_MODELS.copy()

        # ローカルに保存されているモデルを追加（カスタムモデルを含む）
        local_models = self._scan_local_models()
        for model in local_models:
            if model not in available_models:
                available_models.append(model)

        return sorted(available_models)

    def is_valid_model(self, model_name: str) -> bool:
        """モデル名の妥当性をチェック（標準モデル + カスタムモデル）"""
        # 標準モデルまたはローカルに存在するモデルかチェック
        return model_name in self.get_available_models()

    def is_custom_model(self, model_name: str) -> bool:
        """カスタムモデル（ファインチューニング済み）かどうかを判定"""
        return (
            model_name not in STANDARD_MODELS
            and model_name in self._scan_local_models()
        )

    def get_model_path(self, model_name: str) -> str | None:
        """モデルのパスを取得（カスタムモデルの場合はファイルパス、標準モデルの場合はモデル名）"""
        if self.is_custom_model(model_name):
            model_file = self.model_dir / f"{model_name}.pt"
            if model_file.exists():
                return str(model_file)
            return None
        elif model_name in STANDARD_MODELS:
            return model_name
        return None

    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """モデルの準備状態を取得"""
        if not self.is_valid_model(model_name):
            return {
                "model": model_name,
                "is_ready": False,
                "is_loaded": False,
                "is_custom": False,
                "message": f"Invalid model name. Available models: {self.get_available_models()}",
            }

        is_loaded = model_name in self.loaded_models
        is_custom = self.is_custom_model(model_name)

        if is_loaded:
            return {
                "model": model_name,
                "is_ready": True,
                "is_loaded": True,
                "is_custom": is_custom,
                "message": f"{'Custom' if is_custom else 'Standard'} model is loaded and ready",
            }
        else:
            # ロード可能なので準備完了とみなす
            return {
                "model": model_name,
                "is_ready": True,
                "is_loaded": False,
                "is_custom": is_custom,
                "message": f"{'Custom' if is_custom else 'Standard'} model is available but not loaded yet",
            }

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """モデルの詳細情報を取得"""
        if not self.is_valid_model(model_name):
            return {
                "model": model_name,
                "exists": False,
                "message": f"Model not found. Available models: {self.get_available_models()}",
            }

        is_custom = self.is_custom_model(model_name)
        is_loaded = model_name in self.loaded_models

        info = {
            "model": model_name,
            "exists": True,
            "is_custom": is_custom,
            "is_loaded": is_loaded,
            "type": "custom" if is_custom else "standard",
            "file_path": None,
            "file_size": None,
            "last_modified": None,
        }

        if is_custom:
            model_path = self.get_model_path(model_name)
            if model_path:
                model_file = Path(model_path)
                info["file_path"] = str(model_path)
                info["file_size"] = (
                    model_file.stat().st_size if model_file.exists() else 0
                )
                info["last_modified"] = (
                    model_file.stat().st_mtime if model_file.exists() else 0
                )

        return info

    def load_model(self, model_name: str) -> Any:
        if not self.is_valid_model(model_name):
            raise ValueError(
                f"Invalid model name: {model_name}. Available models: {self.get_available_models()}"
            )

        if model_name not in self.loaded_models:
            logger.info(f"Loading Whisper model: {model_name}")

            try:
                if self.is_custom_model(model_name):
                    # カスタムモデル（ファインチューニング済み）のロード
                    model_path = self.get_model_path(model_name)
                    if not model_path:
                        raise ValueError(f"Custom model file not found: {model_name}")

                    logger.info(f"Loading custom model from: {model_path}")
                    model = whisper.load_model(model_path)
                    logger.info(f"Custom model {model_name} loaded successfully")
                else:
                    # 標準モデルのロード
                    # モデルをカスタムディレクトリに保存するための環境変数設定
                    os.environ["WHISPER_CACHE"] = str(self.model_dir)

                    model = whisper.load_model(
                        model_name, download_root=str(self.model_dir)
                    )
                    logger.info(f"Standard model {model_name} loaded successfully")

                self.loaded_models[model_name] = model

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {str(e)}")
                raise Exception(f"Failed to load model {model_name}: {str(e)}")

        return self.loaded_models[model_name]

    def transcribe(
        self, audio_file_path: str, model_name: str = "base", language: str = "ja"
    ) -> Dict[str, Any]:
        model = self.load_model(model_name)

        try:
            logger.info(
                f"Starting transcription for: {audio_file_path} with model: {model_name}"
            )
            result = model.transcribe(audio_file_path, language=language)

            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": result["segments"],
                "model_used": model_name,
            }

        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")


# グローバルインスタンス
whisper_manager = WhisperModelManager()
