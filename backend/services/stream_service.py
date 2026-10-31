# -*- coding: utf-8 -*-
import subprocess
import urllib.parse
from typing import Optional, Tuple, Dict, Any, Generator
from fastapi.responses import StreamingResponse

from backend.core.config import YTDLP_EXE

class StreamService:
    @staticmethod
    def create_stream_response(
        url: str,
        quality: str = "best",
        title: str = "video",
        referer: Optional[str] = None
    ) -> StreamingResponse:
        clean_title = "".join(c for c in title if c not in '\\/:*?"<>|').strip() or "video"
        ref = referer or url

        cmd = [
            YTDLP_EXE,
            "--no-playlist",
            "--referer", ref,
            "-o", "-"
        ]

        if quality.startswith("a"):
            filename = f"{clean_title}.mp3"
            media_type = "audio/mpeg"
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        else:
            filename = f"{clean_title}.mp4"
            media_type = "video/mp4"
            if quality.startswith("v"):
                height_str = quality[1:]
                if height_str.isdigit():
                    h = int(height_str)
                    cmd += [
                        "-f",
                        f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/b[height<={h}][ext=mp4] / bv*[height<={h}]+ba/b[height<={h}] / best",
                        "--merge-output-format", "mp4"
                    ]
                else:
                    cmd += ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]
            else:
                cmd += ["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b", "--merge-output-format", "mp4"]

        cmd.append(url)

        encoded_filename = urllib.parse.quote(filename)
        headers = {
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Content-Type": media_type,
            "Cache-Control": "no-cache"
        }

        def stream_generator() -> Generator[bytes, None, None]:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=64 * 1024
            )
            try:
                while True:
                    chunk = proc.stdout.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk
            finally:
                proc.kill()

        return StreamingResponse(stream_generator(), headers=headers, media_type=media_type)
