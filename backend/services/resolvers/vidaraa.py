# -*- coding: utf-8 -*-
import urllib.parse
from fastapi import HTTPException

from backend.core.config import DEFAULT_HEADERS
from backend.core.security import request_public_url, validate_public_url

def resolve_vidaraa(url: str):
    """
    Extracts direct streaming URL from Vidaraa / Vidara / Vfast server APIs.
    """
    try:
        url = validate_public_url(url)
        filecode = url.rstrip('/').split('/')[-1].split('?')[0]
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        api_url = f"{base}/api/stream"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': DEFAULT_HEADERS['User-Agent'],
            'Referer': url
        }
        data = {'filecode': filecode, 'device': 'web', 'codecs': ['h265', 'av1']}
        r = request_public_url(
            "POST",
            api_url,
            headers=headers,
            json=data,
            timeout=8,
            follow_redirects=False,
        )
        if r.status_code == 200:
            res = r.json()
            stream = res.get('streaming_url')
            title = res.get('title')
            if isinstance(stream, str) and stream:
                stream = validate_public_url(urllib.parse.urljoin(url, stream))
                return stream, title
    except HTTPException:
        return None, None
    except Exception:
        pass
    return None, None
