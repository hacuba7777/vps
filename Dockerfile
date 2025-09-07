FROM python:3.12-slim
WORKDIR /app

# ---- build metadata ----
ARG GIT_SHA=dev
ARG BUILD_TIME=unknown
ARG APP_NAME=myapp
ARG APP_ENV=prod
ENV GIT_SHA=$GIT_SHA BUILD_TIME=$BUILD_TIME APP_NAME=$APP_NAME APP_ENV=$APP_ENV

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# 建使用者 + 切換
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
EXPOSE 8000
CMD ["sh","-c","uvicorn app:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]