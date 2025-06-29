# Whisper音声文字起こしAPI - Backend

FastAPIベースの音声文字起こしサーバーです。

## 🚀 Docker での起動

### 前提条件

1. `.env`ファイルを設定
```bash
# .env.exampleをコピーして設定を調整
cp .env.example .env
```

### 開発環境

```bash
# Dockerコンテナでサーバーを起動
docker compose up --build

# バックグラウンドで起動
docker compose up -d --build

# ログを確認
docker compose logs -f whisper-api
```

### 本番環境

```bash
# docker-compose.ymlのtargetをproductionに変更
# target: development → target: production

docker compose up -d --build
```

### 開発用 vs 本番用の違い

**開発用 (development)**
- 全依存関係インストール (pytest, ruff, mypy等含む)
- uvと仮想環境を使用
- ホットリロード対応
- テスト・開発ツール利用可能

**本番用 (production)**  
- 最小限の依存関係のみ (requirements-prod.txt)
- 仮想環境不使用（軽量化）
- テスト・開発ツール除外
- マルチワーカー対応

### Docker コマンド

```bash
# 設定を確認
docker compose config

# コンテナを停止
docker compose down

# ボリュームも削除（モデルファイルも削除される）
docker compose down -v

# イメージを再ビルド
docker compose build --no-cache

# 特定のサービスのみ再起動
docker compose restart whisper-api
```

## 📋 API エンドポイント

- `GET /health` - ヘルスチェック
- `GET /docs` - Swagger UI（http://localhost:8000/docs）
- `POST /transcribe` - 音声ファイル文字起こし
- `GET /models` - 利用可能なモデル一覧
- `POST /models/{model_name}/load` - モデルロード
- `GET /models/{model_name}/status` - モデル状態確認
- `WebSocket /ws/transcribe` - ストリーミング文字起こし

## 🔧 設定

環境変数またはdocker-compose.ymlで設定を変更できます：

```bash
# 主要設定
APP_NAME="Whisper音声文字起こしAPI"
MODEL_CACHE_DIR="models/whisper"
DEFAULT_MODEL="base"
MAX_FILE_SIZE="26214400"  # 25MB
HOST="0.0.0.0"
PORT="8000"
```

## 🧪 テスト

```bash
# コンテナ内でテスト実行
docker-compose exec whisper-api uv run python -m pytest -v

# ローカル環境でテスト実行
uv run python -m pytest -v
```