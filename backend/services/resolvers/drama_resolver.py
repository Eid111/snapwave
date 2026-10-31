# -*- coding: utf-8 -*-
import re
import requests
from backend.core.config import DEFAULT_HEADERS
from .vidaraa import resolve_vidaraa

def is_rumble_alive(embed_url: str) -> bool:
    try:
        r = requests.get(
            embed_url,
            headers={**DEFAULT_HEADERS, 'Referer': 'https://www.deep-drama.com/'},
            timeout=6
        )
        if r.status_code != 200 or 'Video not found' in r.text or 'video_id":false' in r.text.lower():
            return False
        return True
    except Exception:
        return False

def resolve_drama_site(target_url: str):
    """
    Parses customized drama/series pages to find working embedded servers.
    """
    result = {
        "url": target_url,
        "title": None,
        "referer": target_url,
        "resolved": False,
        "message": ""
    }

    try:
        r = requests.get(target_url, headers=DEFAULT_HEADERS, timeout=12)
        html = r.text
    except Exception as e:
        result["message"] = f"Failed to fetch page: {e}"
        return result

    page_title = None
    m_title = re.search(r'<title>(.*?)</title>', html, re.I)
    if m_title:
        clean_t = re.sub(r'\s*-\s*ديب دراما.*|\s*\|\s*.*', '', m_title.group(1)).strip()
        page_title = clean_t

    servers = []
    for m in re.finditer(r'<button[^>]+data-src=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</button>', html, re.I):
        src, name = m.group(1), m.group(2)
        clean_name = re.sub(r'<[^>]+>', '', name).strip()
        servers.append((clean_name, src))

    for m in re.finditer(r'<iframe[^>]+(?:data-legacy-src|data-src|src)=[\"\']([^\"\']+)[\"\']', html, re.I):
        src = m.group(1)
        if not any(s[1] == src for s in servers):
            servers.append(('Iframe', src))

    if not servers:
        return result

    for name, src in servers:
        if any(v in src.lower() for v in ['vidaraa', 'vidara', 'vfast']):
            stream_url, v_title = resolve_vidaraa(src)
            if stream_url:
                result["url"] = stream_url
                result["title"] = v_title or page_title
                result["referer"] = src
                result["resolved"] = True
                result["message"] = f"تم التحويل تلقائياً لسيرفر ({name})"
                return result

        elif 'rumble.com' in src.lower():
            if is_rumble_alive(src):
                result["url"] = src
                result["title"] = page_title
                result["referer"] = target_url
                result["resolved"] = True
                result["message"] = "سيرفر Rumble متاح ويعمل"
                return result

    return result
