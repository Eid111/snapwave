# -*- coding: utf-8 -*-
import json
import threading
import time
from typing import Any, Dict

from backend.core.config import ADMIN_PASSWORD_ENV, ROOT_DIR
from backend.core.passwords import hash_password, verify_password

CONFIG_FILE = ROOT_DIR / "site_config.json"
_LOCK = threading.RLock()
_PASSWORD_MIGRATION_VERSION = 1
_LEGACY_DEFAULT_PASSWORDS = ("admin", "changeme", "changeme_secure_2026")

DEFAULT_SETTINGS = {
    "site_title": "SnapWave – Video & Audio Fast Downloader",
    "enable_ads": False,
    "direct_ad_url": "",
    "announcement_active": False,
    "announcement_text": "مرحباً بكم في SnapWave – المنصة الأسرع لتحميل الوسائط بجودات أصلية!",
    "rate_limit_per_minute": 25,
    "total_extractions": 0,
    "admin_password_hash": "",
    "last_updated": int(time.time()),
}


def _migrate(data: Dict[str, Any]) -> bool:
    changed = False
    for key, value in DEFAULT_SETTINGS.items():
        if key not in data:
            data[key] = value
            changed = True

    # Remove plaintext password immediately and move to hash
    legacy = data.pop("admin_password", None)
    if legacy:
        changed = True
        if not data.get("admin_password_hash"):
            data["admin_password_hash"] = hash_password(str(legacy))

    if data.get("_admin_password_migration_version") != _PASSWORD_MIGRATION_VERSION:
        stored_hash = data.get("admin_password_hash") or ""
        if any(verify_password(password, stored_hash) for password in _LEGACY_DEFAULT_PASSWORDS):
            data["admin_password_hash"] = hash_password(_configured_admin_password())
        data["_admin_password_migration_version"] = _PASSWORD_MIGRATION_VERSION
        changed = True

    if not data.get("admin_password_hash"):
        data["admin_password_hash"] = hash_password(_configured_admin_password())
        changed = True
    return changed


def _configured_admin_password() -> str:
    if len(ADMIN_PASSWORD_ENV) < 16:
        raise RuntimeError(
            "ADMIN_PASSWORD must be explicitly set to at least 16 characters "
            "before initializing the admin account."
        )
    return ADMIN_PASSWORD_ENV


def _write_unlocked(settings: Dict[str, Any]) -> None:
    payload = dict(settings)
    payload.pop("admin_password", None)
    payload["last_updated"] = int(time.time())
    CONFIG_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_settings() -> Dict[str, Any]:
    with _LOCK:
        if not CONFIG_FILE.exists():
            settings = DEFAULT_SETTINGS.copy()
            _migrate(settings)
            _write_unlocked(settings)
            return settings
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if _migrate(data):
                _write_unlocked(data)
            return data
        except Exception:
            fallback = DEFAULT_SETTINGS.copy()
            _migrate(fallback)
            return fallback


def save_settings(settings: Dict[str, Any]) -> None:
    with _LOCK:
        _migrate(settings)
        _write_unlocked(settings)


def increment_extractions() -> int:
    with _LOCK:
        settings = load_settings()
        settings["total_extractions"] = int(settings.get("total_extractions", 0)) + 1
        _write_unlocked(settings)
        return settings["total_extractions"]
