# -*- coding: utf-8 -*-
from fastapi import APIRouter
from backend.api.v1.endpoints import health, extract, stream

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(extract.router, tags=["Extraction"])
api_v1_router.include_router(stream.router, tags=["Streaming"])
