# -*- coding: utf-8 -*-
import asyncio
import re
import urllib.parse
from typing import Optional

from fastapi.responses import StreamingResponse

from backend.core.config import YTDLP_EXE

AUDIO_PRESETS = {
    "a320": ("mp3", "320K", "audio/mpeg", ".mp3"),
    "a256": ("m4a", "192K", "audio/mp4", ".m4a"),
    "a128": ("mp3", "128K", "audio/mpeg", ".mp3"),
}

STREAM_IDLE_TIMEOUT = 120
MAX_CONCURRENT_DOWNLOADS = 3
_download_slots = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)


class StreamService:
    @staticmethod
    def _safe_filename(title: str) -> str:
        cleaned = "".join(c for c in title if c not in '\\/:*?"<>|').strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return (cleaned[:120] or "video")

    @staticmethod
    async def create_stream_response(
        url: str,
        quality: str = "best",
        title: str = "video",
        referer: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> StreamingResponse:
        clean_title = StreamService._safe_filename(title)
        ref = referer or url
        quality = (quality or "best").strip()[:32]

        cmd = [
            YTDLP_EXE,
            "--no-playlist",
            "--no-warnings",
            "--newline",
            "--referer",
            ref,
            "-o",
            "-",
        ]

        if start_time or end_time:
            start = start_time or "0"
            end = end_time or "999999"
            cmd += ["--download-sections", f"*{start}-{end}"]

        if quality.startswith("a"):
            fmt, audio_q, media_type, ext = AUDIO_PRESETS.get(
                quality, ("mp3", "192K", "audio/mpeg", ".mp3")
            )
            filename = f"{clean_title}{ext}"
            cmd += ["-x", "--audio-format", fmt, "--audio-quality", audio_q]
        else:
            filename = f"{clean_title}.mp4"
            media_type = "video/mp4"
            if quality.startswith("v") and quality[1:].isdigit():
                h = int(quality[1:])
                cmd += [
                    "-f",
                    f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/b[height<={h}][ext=mp4]/bv*[height<={h}]+ba/b[height<={h}]/best",
                    "--merge-output-format",
                    "mp4",
                ]
            else:
                cmd += [
                    "-f",
                    "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
                    "--merge-output-format",
                    "mp4",
                ]

        cmd.append(url)

        encoded_filename = urllib.parse.quote(filename)
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Cache-Control": "no-cache",
            "X-Content-Type-Options": "nosniff",
        }

        async def stream_generator():
            await _download_slots.acquire()
            proc = None
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                assert proc.stdout is not None
                while True:
                    chunk = await asyncio.wait_for(
                        proc.stdout.read(64 * 1024),
                        timeout=STREAM_IDLE_TIMEOUT,
                    )
                    if not chunk:
                        break
                    yield chunk
            except asyncio.TimeoutError:
                return
            finally:
                if proc is not None and proc.returncode is None:
                    proc.kill()
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=5)
                    except Exception:
                        pass
                _download_slots.release()

        return StreamingResponse(stream_generator(), headers=headers, media_type=media_type)
