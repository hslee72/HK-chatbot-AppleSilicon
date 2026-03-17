"""Health check endpoint."""

import httpx
from fastapi import APIRouter

from server.config import OLLAMA_BASE_URL

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    ollama_ok = False
    ollama_models = []

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
                data = resp.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass

    return {
        "status": "ok",
        "ollama": {
            "connected": ollama_ok,
            "base_url": OLLAMA_BASE_URL,
            "models": ollama_models,
        },
    }
