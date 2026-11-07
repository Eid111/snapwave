# -*- coding: utf-8 -*-
import secrets
import time
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.config import APP_TITLE, APP_VERSION
from backend.core.passwords import hash_password, verify_password
from backend.core.security import extract_limiter, get_client_ip, login_limiter, validate_public_url
from backend.core.site_settings import load_settings, save_settings

router = APIRouter()

SESSION_TTL_SECONDS = 12 * 60 * 60
ADMIN_SESSIONS: Dict[str, float] = {}


class LoginRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=256)


class UpdateSettingsRequest(BaseModel):
    enable_ads: Optional[bool] = None
    direct_ad_url: Optional[str] = None
    announcement_active: Optional[bool] = None
    announcement_text: Optional[str] = Field(None, max_length=280)
    rate_limit_per_minute: Optional[int] = Field(None, ge=5, le=300)
    new_admin_password: Optional[str] = Field(None, min_length=8, max_length=128)


def _purge_sessions() -> None:
    now = time.time()
    expired = [token for token, exp in ADMIN_SESSIONS.items() if exp <= now]
    for token in expired:
        ADMIN_SESSIONS.pop(token, None)


def verify_admin(authorization: Optional[str] = Header(None)) -> bool:
    _purge_sessions()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized. Admin authentication required.")

    token = authorization.split(" ", 1)[1].strip()
    expiry = ADMIN_SESSIONS.get(token)

    if not expiry or expiry <= time.time():
        ADMIN_SESSIONS.pop(token, None)
        raise HTTPException(status_code=403, detail="Invalid or expired admin session.")

    # Slide expiration window
    ADMIN_SESSIONS[token] = time.time() + SESSION_TTL_SECONDS
    return True


def apply_runtime_limits(rate_limit: int) -> None:
    extract_limiter.max_requests = rate_limit


@router.get("/config")
async def get_public_config():
    settings = load_settings()
    ad_url = (settings.get("direct_ad_url") or "").strip()
    if ad_url:
        try:
            ad_url = validate_public_url(ad_url)
        except HTTPException:
            ad_url = ""
    return {
        "enable_ads": bool(settings.get("enable_ads", False)),
        "direct_ad_url": ad_url,
        "announcement_active": bool(settings.get("announcement_active", False)),
        "announcement_text": settings.get("announcement_text", ""),
        "version": APP_VERSION,
    }


@router.post("/admin/login")
async def admin_login(req: LoginRequest, request: Request):
    login_limiter.check_rate_limit(get_client_ip(request))
    settings = load_settings()
    stored = settings.get("admin_password_hash") or ""
    if not verify_password(req.password, stored):
        raise HTTPException(status_code=401, detail="Incorrect admin password.")

    _purge_sessions()
    session_token = secrets.token_urlsafe(32)
    ADMIN_SESSIONS[session_token] = time.time() + SESSION_TTL_SECONDS
    return {
        "status": "success",
        "token": session_token,
        "expires_in": SESSION_TTL_SECONDS,
        "message": "Authenticated successfully.",
    }


@router.post("/admin/logout", dependencies=[Depends(verify_admin)])
async def admin_logout(authorization: Optional[str] = Header(None)):
    token = (authorization or "").split(" ", 1)[-1].strip()
    ADMIN_SESSIONS.pop(token, None)
    return {"status": "signed_out"}


@router.get("/admin/settings", dependencies=[Depends(verify_admin)])
async def get_admin_settings():
    settings = load_settings()
    safe_settings = dict(settings)
    safe_settings.pop("admin_password", None)
    safe_settings.pop("_admin_password_migration_version", None)
    safe_settings["admin_password_hash"] = "******"
    safe_settings["metrics"] = {
        "engine_version": APP_VERSION,
        "service": APP_TITLE,
        "active_clients_tracked": len(extract_limiter.clients),
        "total_extractions": settings.get("total_extractions", 0),
    }
    return safe_settings


@router.post("/admin/settings", dependencies=[Depends(verify_admin)])
async def update_admin_settings(req: UpdateSettingsRequest):
    settings = load_settings()

    if req.enable_ads is not None:
        settings["enable_ads"] = req.enable_ads
    if req.direct_ad_url is not None:
        ad_url = req.direct_ad_url.strip()
        if ad_url:
            ad_url = validate_public_url(ad_url)
        settings["direct_ad_url"] = ad_url
    if req.announcement_active is not None:
        settings["announcement_active"] = req.announcement_active
    if req.announcement_text is not None:
        settings["announcement_text"] = req.announcement_text.strip()
    if req.rate_limit_per_minute is not None:
        settings["rate_limit_per_minute"] = req.rate_limit_per_minute
        apply_runtime_limits(req.rate_limit_per_minute)
    if req.new_admin_password:
        settings["admin_password_hash"] = hash_password(req.new_admin_password)
        ADMIN_SESSIONS.clear()

    save_settings(settings)
    return {
        "status": "updated",
        "message": "Settings saved successfully.",
    }
