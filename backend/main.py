# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import APP_TITLE, APP_VERSION, CORS_ORIGINS, FRONTEND_DIR, ROOT_DIR
from backend.api.v1.router import api_v1_router

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="High-performance video & audio extraction API"
)

# Global Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Prevent MIME Sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Prevent Clickjacking
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # Legacy XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Restrict Referrer leakage
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Strict Device Permissions Policy: Block ads from hijacking sensors/hardware
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    # Content Security Policy (Allows Tailwind CDN & Google Fonts, prevents rogue script execution)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: http:; "
        "media-src 'self' blob: data: https: http:; "
        "connect-src 'self' https: http:; "
        "frame-src 'self' https:;"
    )
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend directories
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# Also mount legacy static directory if exists to prevent 404s
legacy_static = ROOT_DIR / "static"
if legacy_static.exists():
    app.mount("/static", StaticFiles(directory=str(legacy_static)), name="static")

# Include API Routers (both /api/v1 and /api for backward compatibility)
app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v1_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    
    # Fallback to legacy static/index.html
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

