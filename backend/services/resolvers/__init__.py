# -*- coding: utf-8 -*-
from typing import Dict, Any
from .drama_resolver import resolve_drama_site

DIRECT_DOMAINS = [
    'youtube.com', 'youtu.be', 'tiktok.com', 'facebook.com', 'fb.watch',
    'instagram.com', 'twitter.com', 'x.com', 'reddit.com', 'vimeo.com'
]

def resolve(target_url: str) -> Dict[str, Any]:
    """
    Main entry point for resolving custom video hostings.
    Skips direct domains that yt-dlp natively supports out of the box.
    """
    url_lower = target_url.lower()
    if any(d in url_lower for d in DIRECT_DOMAINS):
        return {
            "url": target_url,
            "title": None,
            "referer": target_url,
            "resolved": False,
            "message": ""
        }

    return resolve_drama_site(target_url)

__all__ = ["resolve"]
