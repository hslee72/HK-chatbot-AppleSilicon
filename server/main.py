"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from server.config import STATIC_DIR, CHROMA_DIR, TENANTS_DIR
from server.routers import chat, documents, ingest, tenants, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure required directories exist on startup."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    TENANTS_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="HK-chatbot2",
    description="규정 RAG 멀티테넌트 챗봇",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS (dev + Electron) ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(tenants.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(ingest.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# ─── Static SPA serving ──────────────────────────────────────────────────────
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for any non-API route."""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
