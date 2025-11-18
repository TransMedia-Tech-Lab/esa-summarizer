FROM python:3.13-slim

WORKDIR /app

# 依存定義のみ先にコピーしてキャッシュを効かせる
COPY pyproject.toml uv.lock requirements.txt ./

# requirements.txt 経由で依存をインストール（pip 単体）
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体をコピー
COPY bot ./bot
COPY delete_message.py ./delete_message.py

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
# bot ディレクトリをモジュール検索パスに入れる
ENV PYTHONPATH=/app/bot

# Socket Mode の常駐プロセス ＋ 健康チェック用の簡易HTTPサーバ
CMD ["bash", "-lc", "python -m bot.main & python -m http.server ${PORT:-8080}"]
