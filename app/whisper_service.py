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
        """ローカルに保存されたモデルファイルをスキャン"""
        local_models = []
        if self.model_dir.exists():
            # .ptファイルを探す
            for model_file in self.model_dir.glob("*.pt"):
                model_name = model_file.stem
                # 標準的なWhisperモデル名の形式をチェック
                if re.match(r"^(tiny|base|small|medium|large(-v[1-3])?)$", model_name):
                    local_models.append(model_name)
        return local_models

    def get_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得（標準モデル + ローカルモデル）"""
        # 標準モデルから開始
        available_models = STANDARD_MODELS.copy()

        # ローカルに保存されているモデルを追加
        local_models = self._scan_local_models()
        for model in local_models:
            if model not in available_models:
                available_models.append(model)

        return sorted(available_models)

    def is_valid_model(self, model_name: str) -> bool:
        # 標準モデルまたはローカルに存在するモデルかチェック
        return model_name in self.get_available_models()

    def get_model_status(self, model_name: str) -> Dict[str, Any]:
        """モデルの準備状態を取得"""
        if not self.is_valid_model(model_name):
            return {
                "model": model_name,
                "is_ready": False,
                "is_loaded": False,
                "message": f"Invalid model name. Available models: {self.get_available_models()}",
            }

        is_loaded = model_name in self.loaded_models

        if is_loaded:
            return {
                "model": model_name,
                "is_ready": True,
                "is_loaded": True,
                "message": "Model is loaded and ready",
            }
        else:
            # モデルが利用可能だが未ロードの場合
            return {
                "model": model_name,
                "is_ready": True,  # ロード可能なので準備OK
                "is_loaded": False,
                "message": "Model is available but not loaded yet",
            }

    def load_model(self, model_name: str) -> Any:
        if not self.is_valid_model(model_name):
            raise ValueError(
                f"Invalid model name: {model_name}. Available models: {self.get_available_models()}"
            )

        if model_name not in self.loaded_models:
            logger.info(f"Loading Whisper model: {model_name}")

            # モデルをカスタムディレクトリに保存するための環境変数設定
            os.environ["WHISPER_CACHE"] = str(self.model_dir)

            try:
                model = whisper.load_model(
                    model_name, download_root=str(self.model_dir)
                )
                self.loaded_models[model_name] = model
                logger.info(f"Whisper model {model_name} loaded successfully")
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
