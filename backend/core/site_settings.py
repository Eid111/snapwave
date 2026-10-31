# -*- coding: utf-8 -*-
import json
import time
from pathlib import Path
from typing import Dict, Any

from backend.core.config import ROOT_DIR

CONFIG_FILE = ROOT_DIR / "site_config.json"

DEFAULT_SETTINGS = {
    "site_title": "SnapWave – Video & Audio Fast Downloader",
    "enable_ads": False,
    "direct_ad_url": "",
    "announcement_active": False,
    "announcement_text": "مرحباً بكم في SnapWave – المنصة الأسرع لتحميل الوسائط بجودات أصلية!",
    "rate_limit_per_minute": 25,
    "total_extractions": 0,
    "admin_password": "admin",  # Changeable via dashboard
    "last_updated": int(time.time())
}

def load_settings() -> Dict[str, Any]:
    if not CONFIG_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        # Fill missing keys from default if any
        for k, v in DEFAULT_SETTINGS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> None:
    settings["last_updated"] = int(time.time())
    CONFIG_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")

def increment_extractions() -> int:
    settings = load_settings()
    settings["total_extractions"] = settings.get("total_extractions", 0) + 1
    save_settings(settings)
    return settings["total_extractions"]
