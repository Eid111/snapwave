# -*- coding: utf-8 -*-
from typing import Optional

from fastapi import APIRouter, Query, Request

from backend.core.security import download_limiter, get_client_ip, validate_public_url
from backend.services.stream_service import StreamService

router = APIRouter()


@router.get("/download")
@router.get("/stream")
async def download_media_stream(
    request: Request,
    url: str = Query(..., description="Target media URL", max_length=2048),
    quality: str = Query("best", description="Target format ID or quality standard", max_length=32),
    title: str = Query("video", description="Clean video title for filename", max_length=180),
    referer: Optional[str] = Query(None, description="Original referer header", max_length=2048),
    start_time: Optional[str] = Query(None, description="Start time (HH:MM:SS or seconds)", max_length=12),
    end_time: Optional[str] = Query(None, description="End time (HH:MM:SS or seconds)", max_length=12),
):
    # 1. Rate Limit Check
    download_limiter.check_rate_limit(get_client_ip(request))

    # 2. SSRF Validation for target URL
    safe_url = validate_public_url(url)

    # 3. SSRF Validation for referer
    safe_referer = validate_public_url(referer) if referer else safe_url

    return await StreamService.create_stream_response(
        url=safe_url,
        quality=quality,
        title=title,
        referer=safe_referer,
        start_time=start_time,
        end_time=end_time,
    )
