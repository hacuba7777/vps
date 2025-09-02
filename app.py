import os, socket
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse

app = FastAPI()

APP_NAME   = os.getenv("APP_NAME", "myapp")
GIT_SHA    = os.getenv("GIT_SHA", "dev")[:7]
BUILD_TIME = os.getenv("BUILD_TIME", "unknown")
APP_ENV    = os.getenv("APP_ENV", "prod")

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
    <a href="/docs">API Docs</a> · <a href="/healthz">Health</a> · <a href="/version">Version JSON</a>
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
