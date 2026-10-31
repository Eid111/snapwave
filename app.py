# -*- coding: utf-8 -*-
"""
SnapWave - Main Root Runner & ASGI Entrypoint
Delegates cleanly to the modular backend package: backend.main:app
"""
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
