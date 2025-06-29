# カスタムモデル（ファインチューニング済み）の使用方法

本アプリケーションでは、OpenAI Whisperの標準モデルに加えて、ファインチューニング済みのカスタムモデルも使用できます。

## 1. カスタムモデルの配置

ファインチューニング済みのモデルファイル（`.pt`形式）を以下のディレクトリに配置してください：

```
models/whisper/
├── my-custom-model.pt          # カスタムモデル1
├── japanese-news-v1.pt         # カスタムモデル2
└── domain-specific-model.pt    # カスタムモデル3
```

### ファイル命名規則

- ファイル名は英数字、ハイフン（-）、アンダースコア（_）のみ使用可能
- 拡張子は `.pt` 必須
- 例：`medical-terms-v2.pt`、`customer_service_model.pt`

## 2. 利用可能なモデルの確認

### API経由での確認

```bash
# 利用可能なモデル一覧を取得
curl http://localhost:8000/models

# 特定のモデルの情報を取得
curl http://localhost:8000/models/my-custom-model/info
```

### Python経由での確認

```python
from app.services.whisper_service import WhisperModelManager

manager = WhisperModelManager()

# 利用可能なモデル一覧
print("利用可能なモデル:", manager.get_available_models())

# カスタムモデルかどうかの判定
print("カスタムモデル?", manager.is_custom_model("my-custom-model"))

# モデルの詳細情報
info = manager.get_model_info("my-custom-model")
print("モデル情報:", info)
```

## 3. カスタムモデルの使用

### 文字起こしAPI

```bash
# カスタムモデルを使用した音声文字起こし
curl -X POST http://localhost:8000/transcribe \
  -F "file=@audio.wav" \
  -F "model=my-custom-model" \
  -F "language=ja"
```

### WebSocketストリーミング

```bash
# カスタムモデルでストリーミング文字起こし
python demo/streaming.py audio.wav --model my-custom-model --language ja
```

### モデルの事前ロード

```bash
# カスタムモデルを事前にロード（初回のみ時間がかかるため）
curl -X POST http://localhost:8000/models/my-custom-model/load
```

## 4. APIレスポンス例

### モデル一覧

```json
{
  "available_models": [
    "base",
    "japanese-news-v1",
    "large-v1",
    "large-v2",
    "large-v3",
    "medium",
    "my-custom-model",
    "small",
    "tiny"
  ]
}
```

### カスタムモデル情報

```json
{
  "model": "my-custom-model",
  "exists": true,
  "is_custom": true,
  "is_loaded": false,
  "type": "custom",
  "file_path": "models/whisper/my-custom-model.pt",
  "file_size": 1073741824,
  "last_modified": 1625097600.0,
  "message": null
}
```

### 標準モデル情報

```json
{
  "model": "base",
  "exists": true,
  "is_custom": false,
  "is_loaded": false,
  "type": "standard",
  "file_path": null,
  "file_size": null,
  "last_modified": null,
  "message": null
}
```

## 5. モデル管理のベストプラクティス

### モデルファイルの管理

1. **バージョン管理**: モデル名にバージョンを含める（例：`model-v1.pt`、`model-v2.pt`）
2. **用途別分類**: 用途に応じた命名（例：`medical-transcription.pt`、`customer-service.pt`）
3. **バックアップ**: 重要なモデルは別途バックアップを保管

### パフォーマンス最適化

1. **事前ロード**: よく使用するカスタムモデルは事前にロードしておく
2. **メモリ管理**: 不要なモデルは適宜アンロード（現在の実装では手動管理）
3. **ファイルサイズ**: 大きなモデルファイルはディスク容量とロード時間に注意

## 6. トラブルシューティング

### モデルが認識されない

- ファイル名に無効な文字が含まれていないか確認
- `.pt` 拡張子が正しく付いているか確認
- `models/whisper/` ディレクトリに配置されているか確認

### ロードエラー

- モデルファイルが破損していないか確認
- ファイルサイズとディスク容量を確認
- ログを確認してエラーの詳細を把握

### メモリ不足

- 複数の大きなモデルを同時にロードしていないか確認
- システムのメモリ使用量を監視
- 必要に応じて不要なモデルをアンロード

## 7. 技術仕様

### サポートされるモデル形式

- **標準モデル**: OpenAI Whisperの公式モデル（tiny, base, small, medium, large-v1/v2/v3）
- **カスタムモデル**: PyTorchの`.pt`形式でファインチューニングされたWhisperモデル

### API仕様

- **GET** `/models` - 利用可能なモデル一覧
- **GET** `/models/{model_name}/status` - モデルの状態確認
- **GET** `/models/{model_name}/info` - モデルの詳細情報
- **POST** `/models/{model_name}/load` - モデルの事前ロード
- **POST** `/transcribe` - 音声文字起こし（`model`パラメータでカスタムモデル指定可能）
- **WebSocket** `/stream-transcribe` - ストリーミング文字起こし（`model`パラメータ対応）
