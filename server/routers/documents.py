"""Document listing endpoint."""

from fastapi import APIRouter

from server.rag.ingestion import get_document_list

router = APIRouter(tags=["documents"])


@router.get("/documents")
async def list_documents(tenant_id: str = "default"):
    """Return ingested documents with title, summary, page count."""
    return get_document_list(tenant_id)
