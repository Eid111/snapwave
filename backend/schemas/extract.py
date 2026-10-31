# -*- coding: utf-8 -*-
from typing import List, Optional
from pydantic import BaseModel, Field

class ExtractRequest(BaseModel):
    url: str = Field(..., description="The media URL to inspect and download")

class FormatItem(BaseModel):
    id: str
    type: str  # 'video' or 'audio'
    container: str  # 'MP4', 'MP3', 'M4A'
    res: str  # '1080p', '320 kbps', etc.
    tag: str  # 'FHD', 'HD', 'High', etc.
    codec: str  # 'H.264 · AAC', etc.
    mb: float  # Estimated size in megabytes

class ExtractResponse(BaseModel):
    host: str
    title: str
    author: str
    duration: int
    date: str
    thumbnail: str
    target_url: str
    referer: Optional[str] = None
    formats: List[FormatItem]
