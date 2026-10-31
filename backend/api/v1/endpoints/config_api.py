# -*- coding: utf-8 -*-
import time
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Header, Depends

from backend.core.config import APP_VERSION, APP_TITLE
from backend.core.site_settings import load_settings, save_settings
from backend.core.security import extract_limiter

router = APIRouter()

# In-memory simple auth tokens for admin sessions
ADMIN_SESSIONS = set()

class LoginRequest(BaseModel):
    password: str

class UpdateSettingsRequest(BaseModel):
    enable_ads: Optional[bool] = None
    direct_ad_url: Optional[str] = None
    announcement_active: Optional[bool] = None
    announcement_text: Optional[str] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=5, le=300)
    new_admin_password: Optional[str] = Field(None, min_length=4)

def verify_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized. Admin authentication required.")
    token = authorization.split(" ")[1]
    if token not in ADMIN_SESSIONS:
        raise HTTPException(status_code=403, detail="Invalid or expired admin session.")
    return True

@router.get("/config")
async def get_public_config():
    """
    Public configuration loaded by client apps & frontend on initialization.
    """
    settings = load_settings()
    return {
        "enable_ads": settings.get("enable_ads", False),
        "direct_ad_url": settings.get("direct_ad_url", ""),
        "announcement_active": settings.get("announcement_active", False),
        "announcement_text": settings.get("announcement_text", ""),
        "version": APP_VERSION
    }

@router.post("/admin/login")
async def admin_login(req: LoginRequest):
    settings = load_settings()
    correct_pass = settings.get("admin_password", "admin")
    if req.password != correct_pass:
        raise HTTPException(status_code=401, detail="Incorrect admin password.")
    
    # Generate session token
    session_token = f"snapwave_admin_{int(time.time())}"
    ADMIN_SESSIONS.add(session_token)
    return {
        "status": "success",
        "token": session_token,
        "message": "Authenticated successfully."
    }

@router.get("/admin/settings", dependencies=[Depends(verify_admin)])
async def get_admin_settings():
    settings = load_settings()
    # Mask password for security
    safe_settings = settings.copy()
    safe_settings["admin_password"] = "******"
    
    # Add system metrics
    safe_settings["metrics"] = {
        "engine_version": APP_VERSION,
        "active_clients_tracked": len(extract_limiter.clients),
        "total_extractions": settings.get("total_extractions", 0)
    }
    return safe_settings

@router.post("/admin/settings", dependencies=[Depends(verify_admin)])
async def update_admin_settings(req: UpdateSettingsRequest):
    settings = load_settings()
    
    if req.enable_ads is not None:
        settings["enable_ads"] = req.enable_ads
    if req.direct_ad_url is not None:
        settings["direct_ad_url"] = req.direct_ad_url.strip()
    if req.announcement_active is not None:
        settings["announcement_active"] = req.announcement_active
    if req.announcement_text is not None:
        settings["announcement_text"] = req.announcement_text.strip()
    if req.rate_limit_per_minute is not None:
        settings["rate_limit_per_minute"] = req.rate_limit_per_minute
        extract_limiter.max_requests = req.rate_limit_per_minute
    if req.new_admin_password:
        settings["admin_password"] = req.new_admin_password
        
    save_settings(settings)
    return {
        "status": "updated",
        "message": "Settings saved successfully."
    }
