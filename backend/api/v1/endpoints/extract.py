# -*- coding: utf-8 -*-
from fastapi import APIRouter, Request

from backend.core.security import extract_limiter, get_client_ip
from backend.schemas.extract import ExtractRequest, ExtractResponse
from backend.services.ytdlp_service import YtDlpService

router = APIRouter()


@router.post("/extract", response_model=ExtractResponse)
async def extract_video_info(req: ExtractRequest, request: Request):
    extract_limiter.check_rate_limit(get_client_ip(request))
    return await YtDlpService.extract_info(req.url)
