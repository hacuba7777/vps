FROM python:3.12-slim
WORKDIR /app

# ---- build metadata ----
ARG GIT_SHA=dev
ARG BUILD_TIME=unknown
ARG APP_NAME=myapp
ARG APP_ENV=prod
ENV GIT_SHA=$GIT_SHA BUILD_TIME=$BUILD_TIME APP_NAME=$APP_NAME APP_ENV=$APP_ENV

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
