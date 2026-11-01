# -*- coding: utf-8 -*-
"""
SnapWave - Production ASGI Entrypoint
Runs seamlessly on Local, Docker, Zeabur, Render, and Cloud Containers
"""
import os
import uvicorn
from backend.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port)
