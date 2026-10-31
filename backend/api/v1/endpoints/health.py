# -*- coding: utf-8 -*-
from fastapi import APIRouter
from backend.core.config import APP_VERSION, APP_TITLE

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "engine": f"v{APP_VERSION}",
        "service": APP_TITLE
    }
