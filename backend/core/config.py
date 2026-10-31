# -*- coding: utf-8 -*-
import os
import sys
import shutil
from pathlib import Path

# Paths configuration
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
BIN_DIR = ROOT_DIR / "bin"

# Locate yt-dlp binary with cross-platform fallback (Windows & Linux Cloud)
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

# Application metadata
APP_TITLE = "SnapWave Video & Audio Downloader"
APP_VERSION = "2.5.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Allowed CORS origins
CORS_ORIGINS = ["*"]

# Standard browser headers for web scraping
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
