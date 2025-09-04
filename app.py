import os, socket
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse

# NEW: 引入 Prometheus client 與 time，提供 /metrics 與請求計數/延遲
from time import time  # NEW: 計時用來量測請求延遲
from prometheus_client import (  # NEW
    Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
)

app = FastAPI()

APP_NAME   = os.getenv("APP_NAME", "myapp")
GIT_SHA    = os.getenv("GIT_SHA", "dev")[:7]
BUILD_TIME = os.getenv("BUILD_TIME", "unknown")
APP_ENV    = os.getenv("APP_ENV", "prod")

# ---------------- Prometheus 指標定義（零侵入，通用） ----------------
# NEW: 計數器：統計 HTTP 請求總數，按路徑/方法/狀態碼分維度
REQUESTS = Counter(
    "http_requests_total",                  # metrics 名稱（Prometheus 慣例：小寫+底線）
    "Total HTTP requests",                  # 說明文字
    ["path", "method", "status"]            # 標籤：用來切分不同路徑/方法/狀態碼
)

# NEW: 直方圖：觀察每個請求的耗時（秒），按路徑/方法分維度做分佈統計
REQ_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["path", "method"]
)

# NEW: 量表：目前正在處理中的請求數；進來 +1、處理完 -1
INPROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress"
)

# NEW: FastAPI 中介層（middleware）— 自動為每個請求計數、計時、記錄狀態碼
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method

    # 🚫 跳過 /metrics 本身，避免監控請求污染數據
    if path == "/metrics":
        return await call_next(request)

    INPROGRESS.inc()          # 有請求進來 → in-progress +1
    start = time()            # 記錄開始時間

    try:
        response = await call_next(request)   # 繼續處理請求
        # 記錄請求完成：依 path/method/status 累加 Counter
        REQUESTS.labels(path=path, method=method, status=str(response.status_code)).inc()
        return response
    finally:
        INPROGRESS.dec()      # 請求結束 → in-progress -1
        REQ_LATENCY.labels(path=path, method=method).observe(time() - start)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    host = socket.gethostname()
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{APP_NAME} status</title>
<style>
  body{{font-family:ui-sans-serif,system-ui;margin:2rem;line-height:1.5}}
  .grid{{display:grid;grid-template-columns:140px 1fr;gap:.5rem 1rem;max-width:700px}}
  code{{background:#f6f8fa;padding:.2rem .4rem;border-radius:6px}}
  a{{text-decoration:none}}
</style></head>
<body>
  <h1>✅ {APP_NAME} is running</h1>
  <div class="grid">
    <div>Version</div><div><code>{GIT_SHA}</code></div>
    <div>Build</div><div>{BUILD_TIME}</div>
    <div>Env</div><div>{APP_ENV}</div>
    <div>Host</div><div>{host}</div>
  </div>
  <p style="margin-top:1rem">
    <a href="/docs">API Docs</a> · <a href="/healthz">Health</a> · <a href="/version">Version JSON</a> · <a href="/metrics">Metrics</a>  <!-- NEW: 方便點到 /metrics -->
  </p>
</body></html>"""
    return HTMLResponse(html)

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.head("/healthz")
def healthz_head():
    return Response(status_code=200)

@app.get("/version")
def version():
    return JSONResponse({"sha": GIT_SHA, "build_time": BUILD_TIME, "env": APP_ENV, "name": APP_NAME})

# NEW: Prometheus 抓數據的端點，導出目前所有 metrics
@app.get("/metrics")
def metrics():
    # NEW: generate_latest() 會把已註冊的 metrics 轉成 Prometheus 可讀的純文字格式
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
