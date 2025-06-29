FROM python:3.12-slim

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

ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]