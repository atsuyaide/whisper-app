# 開発用ステージ
FROM python:3.12-slim as development

# 必要な環境変数を設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システムの依存関係をインストール（開発用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# uvをインストール（開発用）
RUN pip install --no-cache-dir uv

# 作業ディレクトリを設定
WORKDIR /app

# 開発用依存関係をインストール
COPY requirements.txt .
RUN uv venv && uv pip install --no-cache -r requirements.txt

# ソースコードをコピー
COPY . .

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# 本番用ステージ（軽量）
FROM python:3.12-slim as production

# 必要な環境変数を設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# システムの依存関係をインストール（最小限）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 作業ディレクトリを設定
WORKDIR /app

# 本番用依存関係のみインストール（仮想環境不使用）
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# ソースコードをコピー
COPY app/ ./app/

# ヘルスチェックを設定
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]