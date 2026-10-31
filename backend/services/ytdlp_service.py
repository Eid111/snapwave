# -*- coding: utf-8 -*-
import json
import subprocess
import urllib.parse
from typing import Dict, Any, List
from fastapi import HTTPException

from backend.core.config import YTDLP_EXE
from backend.core.security import validate_public_url
from backend.core.site_settings import increment_extractions
from backend.services.resolvers import resolve

class YtDlpService:
    @staticmethod
    def extract_info(raw_url: str) -> Dict[str, Any]:
        # Enforce strict URL validation & anti-SSRF protections
        url = validate_public_url(raw_url)

        # 1. Resolve custom/drama links if applicable
        res_data = resolve(url)
        target_url = res_data["url"]
        referer = res_data.get("referer") or target_url
        custom_title = res_data.get("title")

        # 2. Query yt-dlp binary for JSON metadata
        cmd = [
            YTDLP_EXE,
            "--dump-json",
            "--no-playlist",
            "--referer", referer,
            target_url
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=30
            )
            if proc.returncode != 0 or not proc.stdout.strip():
                err_msg = proc.stderr.strip() or "Failed to inspect video link"
                if "Video not found" in err_msg or "HTTP Error 404" in err_msg:
                    err_msg = "Video is private, removed, or not found on the host."
                elif "HTTP Error 403" in err_msg:
                    err_msg = "Access restricted or rate limited by the host."
                raise HTTPException(status_code=400, detail=err_msg)

            data = json.loads(proc.stdout.strip().split("\n")[-1])
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Request timed out while probing stream.")
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse stream metadata.")

        # 3. Parse core metadata
        title = custom_title or data.get("title") or "video"
        thumbnail = data.get("thumbnail") or "/assets/favicon.svg"
        duration = int(data.get("duration") or 0)
        author = data.get("uploader") or data.get("channel") or data.get("creator") or "Unknown Creator"

        # Host extraction
        parsed_host = urllib.parse.urlparse(url).netloc.replace("www.", "")
        host = parsed_host or (data.get("extractor") or "web")

        # 4. Formats construction
        raw_formats = data.get("formats") or []
        formats_list: List[Dict[str, Any]] = []
        seen_heights = set()

        for f in sorted(raw_formats, key=lambda x: x.get("height") or 0, reverse=True):
            h = f.get("height")
            if not h or h < 240:
                continue

            bucket = None
            for std in [2160, 1440, 1080, 720, 480, 360]:
                if h >= (std - 30) and std not in seen_heights:
                    bucket = std
                    break

            if bucket:
                seen_heights.add(bucket)
                tag_map = {2160: "4K UHD", 1440: "2K QHD", 1080: "FHD", 720: "HD", 480: "SD", 360: "Low"}
                tag = tag_map.get(bucket, "HD")

                dur = duration if duration > 0 else 180
                filesize = f.get("filesize") or f.get("filesize_approx")
                if filesize:
                    mb = round(filesize / (1024 * 1024), 1)
                else:
                    tbr = f.get("tbr") or (bucket * 3.5)
                    mb = round((tbr * 1000 * dur) / (8 * 1024 * 1024), 1)

                vcodec = (f.get("vcodec") or "AVC").upper()
                if "AVC" in vcodec or "H264" in vcodec:
                    codec_disp = "H.264 · AAC"
                elif "VP9" in vcodec or "VP09" in vcodec:
                    codec_disp = "VP9 · Opus"
                elif "AV01" in vcodec or "AV1" in vcodec:
                    codec_disp = "AV1 · AAC"
                else:
                    codec_disp = "AVC · AAC"

                formats_list.append({
                    "id": f"v{bucket}",
                    "type": "video",
                    "container": "MP4",
                    "res": f"{bucket}p",
                    "tag": tag,
                    "codec": codec_disp,
                    "mb": max(mb, 2.5)
                })

        if not formats_list:
            formats_list.append({
                "id": "best",
                "type": "video",
                "container": "MP4",
                "res": "Original",
                "tag": "Best",
                "codec": "H.264 · AAC",
                "mb": 42.0
            })

        # Standard Audio streams
        dur = duration if duration > 0 else 180
        formats_list.append({
            "id": "a320",
            "type": "audio",
            "container": "MP3",
            "res": "320 kbps",
            "tag": "High",
            "codec": "MP3 · CBR",
            "mb": round((320 * 1000 * dur) / (8 * 1024 * 1024), 1)
        })
        formats_list.append({
            "id": "a256",
            "type": "audio",
            "container": "M4A",
            "res": "256 kbps",
            "tag": "High",
            "codec": "AAC-LC",
            "mb": round((256 * 1000 * dur) / (8 * 1024 * 1024), 1)
        })
        formats_list.append({
            "id": "a128",
            "type": "audio",
            "container": "MP3",
            "res": "128 kbps",
            "tag": "Standard",
            "codec": "MP3 · CBR",
            "mb": round((128 * 1000 * dur) / (8 * 1024 * 1024), 1)
        })

        # Record successful extraction metric
        try:
            increment_extractions()
        except Exception:
            pass

        return {
            "host": host,
            "title": title,
            "author": author,
            "duration": duration,
            "date": "Available now",
            "thumbnail": thumbnail,
            "target_url": target_url,
            "referer": referer,
            "formats": formats_list
        }
