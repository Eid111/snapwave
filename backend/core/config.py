# -*- coding: utf-8 -*-
import os
import shutil
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
BIN_DIR = ROOT_DIR / "bin"

if (BIN_DIR / "yt-dlp.exe").exists():
    YTDLP_EXE = str(BIN_DIR / "yt-dlp.exe")
elif (ROOT_DIR / "yt-dlp.exe").exists():
    YTDLP_EXE = str(ROOT_DIR / "yt-dlp.exe")
elif (BIN_DIR / "yt-dlp").exists():
    YTDLP_EXE = str(BIN_DIR / "yt-dlp")
elif shutil.which("yt-dlp"):
    YTDLP_EXE = shutil.which("yt-dlp")
else:
    YTDLP_EXE = "yt-dlp"

APP_TITLE = os.getenv("APP_TITLE", "SnapWave Video & Audio Downloader")
APP_VERSION = "2.6.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"
ADMIN_PASSWORD_ENV = os.getenv("ADMIN_PASSWORD", "").strip()

_raw_origins = os.getenv("CORS_ORIGINS", "*").strip()
if not _raw_origins or _raw_origins == "*":
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
else:
    CORS_ORIGINS = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]
    CORS_ALLOW_CREDENTIALS = True

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
