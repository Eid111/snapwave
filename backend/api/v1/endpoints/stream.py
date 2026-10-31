# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Query
from backend.services.stream_service import StreamService

router = APIRouter()

@router.get("/download")
@router.get("/stream")
async def download_media_stream(
    url: str = Query(..., description="Target media URL"),
    quality: str = Query("best", description="Target format ID or quality standard"),
    title: str = Query("video", description="Clean video title for filename"),
    referer: Optional[str] = Query(None, description="Original referer header")
):
    return StreamService.create_stream_response(
        url=url,
        quality=quality,
        title=title,
        referer=referer
    )
