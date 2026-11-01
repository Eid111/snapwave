# -*- coding: utf-8 -*-
"""
SnapWave - Production ASGI Entrypoint & Cloud Spaces Runner
Supports: Local, Docker, and Hugging Face ZeroGPU Spaces
"""
import os
import sys
from pathlib import Path

# ZeroGPU Compatibility Layer
try:
    import spaces
    @spaces.GPU
    def hf_zerogpu_hook():
        return True
except Exception:
    pass

import gradio as gr
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from backend.main import app as fastapi_app
from backend.core.config import FRONTEND_DIR

# Custom Fullscreen Web Wrapper for Gradio
custom_css = """
footer { display: none !important; }
.gradio-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }
#snapwave-frame { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 999999; }
"""

with gr.Blocks(title="SnapWave – Fast Video & Audio Downloader", css=custom_css) as demo:
    gr.HTML("""
    <iframe id="snapwave-frame" src="/app" allow="clipboard-read; clipboard-write"></iframe>
    """)

# Mount all FastAPI routes and assets directly to Gradio's internal ASGI app
demo.app.mount("/app", fastapi_app)
if FRONTEND_DIR.exists():
    demo.app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    demo.app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    demo.app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# Include API routers directly onto root for direct fetch calls
demo.app.include_router(fastapi_app.router)

if __name__ == "__main__":
    # Gradio handles ZeroGPU port bindings automatically
    demo.launch(server_name="0.0.0.0")
