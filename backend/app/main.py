from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="GainCheck")

# CORS: lets the Streamlit app (running on another port) call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_methods=["*"],
    allow_headers=["*"],
)

# All v1 routes live under /api/v1, for example /api/v1/health
app.include_router(api_router, prefix="/api/v1")
