# -*- coding: utf-8 -*-
import sys
import re
import json
import urllib.parse
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def is_rumble_alive(embed_url):
    try:
        r = requests.get(embed_url, headers={**HEADERS, 'Referer': 'https://www.deep-drama.com/'}, timeout=6)
        if r.status_code != 200 or 'Video not found' in r.text or 'video_id":false' in r.text.lower():
            return False
        return True
    except:
        return False

def resolve_vidaraa(url):
    try:
        filecode = url.rstrip('/').split('/')[-1].split('?')[0]
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        api_url = f"{base}/api/stream"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': HEADERS['User-Agent'],
            'Referer': url
        }
        data = {'filecode': filecode, 'device': 'web', 'codecs': ['h265', 'av1']}
        r = requests.post(api_url, headers=headers, json=data, timeout=8)
        if r.status_code == 200:
            res = r.json()
            stream = res.get('streaming_url')
            title = res.get('title')
            return stream, title
    except:
        pass
    return None, None

def resolve(target_url):
    result = {
        "url": target_url,
        "title": None,
        "referer": target_url,
        "resolved": False,
        "message": ""
    }

    direct_domains = ['youtube.com', 'youtu.be', 'tiktok.com', 'facebook.com', 'fb.watch', 'instagram.com', 'twitter.com', 'x.com', 'reddit.com', 'vimeo.com']
    if any(d in target_url.lower() for d in direct_domains):
        return result

    try:
        r = requests.get(target_url, headers=HEADERS, timeout=12)
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
                result["message"] = f"تم التحويل تلقائياً لسيرفر ({name}) الشغال"
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