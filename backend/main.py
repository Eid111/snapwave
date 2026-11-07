# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.api.v1.endpoints.config_api import apply_runtime_limits
from backend.api.v1.router import api_v1_router
from backend.core.config import (
    ADMIN_PASSWORD_ENV,
    APP_TITLE,
    APP_VERSION,
    CORS_ALLOW_CREDENTIALS,
    CORS_ORIGINS,
    FRONTEND_DIR,
    ROOT_DIR,
)
from backend.core.site_settings import load_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if len(ADMIN_PASSWORD_ENV) < 16:
        raise RuntimeError(
            "ADMIN_PASSWORD must be explicitly set to at least 16 characters "
            "before starting the app."
        )
    settings = load_settings()
    apply_runtime_limits(int(settings.get("rate_limit_per_minute", 25)))
    yield


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="High-performance video & audio extraction API",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'self'; "
        "form-action 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: http:; "
        "media-src 'self' blob: data: https: http:; "
        "connect-src 'self'; "
        "frame-src 'self';"
    )
    return response


# Adjusted CORS configuration for security
if CORS_ORIGINS == ["*"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False if allow_origins is ["*"]
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

legacy_static = ROOT_DIR / "static"
if legacy_static.exists():
    app.mount("/static", StaticFiles(directory=str(legacy_static)), name="static")

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v1_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    legacy_index = ROOT_DIR / "static" / "index.html"
    if legacy_index.exists():
        return HTMLResponse(content=legacy_index.read_text(encoding="utf-8"))

    return HTMLResponse("<h1>SnapWave Engine Online</h1>")


@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    fav = FRONTEND_DIR / "assets" / "favicon.svg"
    if fav.exists():
        return FileResponse(str(fav), media_type="image/svg+xml")
    return HTMLResponse("")


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    admin_file = FRONTEND_DIR / "admin.html"
    if admin_file.exists():
        return HTMLResponse(content=admin_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>SnapWave Admin Dashboard</h1>")


@app.get("/robots.txt", response_class=PlainTextResponse)
async def serve_robots(request: Request):
    host_url = f"{request.url.scheme}://{request.url.netloc}"
    return f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/

Sitemap: {host_url}/sitemap.xml
"""


@app.get("/sitemap.xml")
async def serve_sitemap(request: Request):
    host_url = f"{request.url.scheme}://{request.url.netloc}"
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{host_url}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return Response(content=xml_content, media_type="application/xml")
