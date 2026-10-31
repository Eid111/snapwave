# -*- coding: utf-8 -*-
from fastapi import APIRouter, Request
from backend.schemas.extract import ExtractRequest, ExtractResponse
from backend.services.ytdlp_service import YtDlpService
from backend.core.security import extract_limiter

router = APIRouter()

@router.post("/extract", response_model=ExtractResponse)
async def extract_video_info(req: ExtractRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    # Protect against bot flood / spam
    extract_limiter.check_rate_limit(client_ip)
    return YtDlpService.extract_info(req.url)
