FROM python:3.11-slim

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリを設定
WORKDIR /app

# 複数のデータ保存場所を作成
RUN mkdir -p /workspace/data /tmp/notifications /var/tmp/notifications /app/data && \
    chmod 777 /workspace/data /tmp/notifications /var/tmp/notifications /app/data

# Pythonパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

# 環境変数設定
ENV PYTHONPATH=/app
ENV PRODUCTION_MODE=true
ENV NOTIFICATION_STORAGE_PATH=/tmp/notifications.json
ENV NOTIFICATION_CHECK_INTERVAL=30
ENV PERSISTENT_STORAGE_ENABLED=true

# ポート8000を公開
EXPOSE 8000

# ヘルスチェック追加
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# アプリケーションを起動
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app:app"]