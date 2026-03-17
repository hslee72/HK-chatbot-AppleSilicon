"""Document ingestion endpoint."""

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.config import DATA_DIR
from server.rag.ingestion import ingest_pdfs
from server.tenants.manager import get_tenant, ensure_default_tenant

router = APIRouter(tags=["ingest"])


class IngestRequest(BaseModel):
    tenant_id: str = "default"
    filenames: list[str] | None = None  # None = ingest all PDFs in data/


@router.post("/ingest")
async def ingest_documents(req: IngestRequest):
    """Ingest PDFs from ./data into tenant's vector store."""
    ensure_default_tenant()

    tenant = get_tenant(req.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Resolve PDF paths
    pdf_paths: list[Path] | None = None
    if req.filenames:
        pdf_paths = []
        for fn in req.filenames:
            p = DATA_DIR / fn
            if not p.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {fn}")
            pdf_paths.append(p)

    # Run ingestion in thread pool (CPU-bound)
    result = await asyncio.to_thread(ingest_pdfs, req.tenant_id, pdf_paths)
    return result


@router.get("/ingest/files")
async def list_available_files():
    """List PDF files available in ./data for ingestion."""
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    return [{"filename": p.name, "size_mb": round(p.stat().st_size / 1e6, 2)} for p in pdfs]
