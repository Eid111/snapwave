# -*- coding: utf-8 -*-
import urllib.parse
import requests
from backend.core.config import DEFAULT_HEADERS

def resolve_vidaraa(url: str):
    """
    Extracts direct streaming URL from Vidaraa / Vidara / Vfast server APIs.
    """
    try:
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
        r = requests.post(api_url, headers=headers, json=data, timeout=8)
        if r.status_code == 200:
            res = r.json()
            stream = res.get('streaming_url')
            title = res.get('title')
            return stream, title
    except Exception:
        pass
    return None, None
