# -*- coding: utf-8 -*-
"""
SnapWave - Production ASGI Entrypoint & Cloud Spaces Runner
Supports: Local, Docker, and Hugging Face Spaces
"""
import os
import sys
from backend.main import app as fastapi_app

# If running inside Hugging Face Spaces (Gradio SDK)
try:
    import gradio as gr
    # Create companion Gradio block for Hugging Face healthcheck
    with gr.Blocks(title="SnapWave Engine") as demo:
        gr.HTML("""
        <div style="text-align:center; padding: 20px; font-family:sans-serif;">
            <h2>🚀 SnapWave Video & Audio Downloader Engine</h2>
            <p>The system is online. Click below to enter the full web application:</p>
            <a href="/" target="_self" style="display:inline-block; padding:10px 24px; background:#FF5500; color:white; border-radius:8px; text-decoration:none; font-weight:bold;">Open SnapWave App</a>
        </div>
        """)

    # Mount Gradio at /gradio so root '/' serves our custom UI directly
    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
except ImportError:
    app = fastapi_app
    demo = None

if __name__ == "__main__":
    import uvicorn
    # Hugging Face Spaces standard port is 7860, local default is 8000
    default_port = 7860 if "SPACE_ID" in os.environ else 8000
    port = int(os.environ.get("PORT", default_port))
    uvicorn.run(app, host="0.0.0.0", port=port)
