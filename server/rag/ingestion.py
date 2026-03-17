"""PDF ingestion pipeline: parse → chunk → embed → store in ChromaDB."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from pypdf import PdfReader

from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from server.config import (
    CHROMA_DIR,
    DATA_DIR,
    TENANTS_DIR,
    EMBED_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

logger = logging.getLogger(__name__)


# ─── Document metadata ────────────────────────────────────────────────────────

def _extract_pdf_metadata(pdf_path: Path) -> dict:
    """Extract title, page count, and summary from a PDF file."""
    reader = PdfReader(str(pdf_path))
    page_count = len(reader.pages)

    # Title: try PDF metadata first, fall back to filename
    info = reader.metadata
    title = None
    if info and info.title and info.title.strip():
        title = info.title.strip()
    if not title:
        title = pdf_path.stem  # filename without extension

    # Summary: first 200 chars of first page text
    summary = ""
    if page_count > 0:
        first_page_text = reader.pages[0].extract_text() or ""
        summary = first_page_text[:200].replace("\n", " ").strip()
        if len(first_page_text) > 200:
            summary += "…"

    return {
        "title": title,
        "page_count": page_count,
        "summary": summary,
        "filename": pdf_path.name,
    }


def _save_document_metadata(tenant_id: str, doc_meta: dict) -> None:
    """Persist document metadata to tenant's JSON store."""
    meta_dir = TENANTS_DIR / tenant_id
    meta_dir.mkdir(parents=True, exist_ok=True)
    meta_file = meta_dir / "documents.json"

    docs = []
    if meta_file.exists():
        docs = json.loads(meta_file.read_text(encoding="utf-8"))

    # Avoid duplicates by filename
    docs = [d for d in docs if d["filename"] != doc_meta["filename"]]
    doc_meta["ingested_at"] = datetime.now(timezone.utc).isoformat()
    docs.append(doc_meta)

    meta_file.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")


def get_document_list(tenant_id: str) -> list[dict]:
    """Return metadata for all ingested documents of a tenant."""
    meta_file = TENANTS_DIR / tenant_id / "documents.json"
    if not meta_file.exists():
        return []
    return json.loads(meta_file.read_text(encoding="utf-8"))


# ─── PDF → LlamaIndex Documents ──────────────────────────────────────────────

def _pdf_to_documents(pdf_path: Path) -> list[Document]:
    """Parse a single PDF into LlamaIndex Document objects (one per page)."""
    reader = PdfReader(str(pdf_path))
    documents = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if not text or not text.strip():
            continue
        doc = Document(
            text=text,
            metadata={
                "source": pdf_path.name,
                "page": page_num,
                "total_pages": len(reader.pages),
            },
        )
        documents.append(doc)
    return documents


# ─── Main ingestion ──────────────────────────────────────────────────────────

def ingest_pdfs(
    tenant_id: str,
    pdf_paths: list[Path] | None = None,
) -> dict:
    """
    Ingest PDF files into tenant-specific ChromaDB collection.

    Args:
        tenant_id: Target tenant identifier.
        pdf_paths: Specific PDFs to ingest. If None, ingest all PDFs in DATA_DIR.

    Returns:
        Summary dict with counts and metadata.
    """
    if pdf_paths is None:
        pdf_paths = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_paths:
        return {"status": "no_files", "ingested": 0, "documents": []}

    # Collect all documents
    all_docs: list[Document] = []
    doc_metadata_list: list[dict] = []

    for pdf_path in pdf_paths:
        logger.info("Parsing: %s", pdf_path.name)
        try:
            meta = _extract_pdf_metadata(pdf_path)
            docs = _pdf_to_documents(pdf_path)
            all_docs.extend(docs)
            doc_metadata_list.append(meta)
            _save_document_metadata(tenant_id, meta)
            logger.info(
                "  → %d pages, %d chunks from %s",
                meta["page_count"],
                len(docs),
                pdf_path.name,
            )
        except Exception as e:
            logger.error("Failed to parse %s: %s", pdf_path.name, e)
            doc_metadata_list.append({
                "filename": pdf_path.name,
                "title": pdf_path.stem,
                "page_count": 0,
                "summary": f"Error: {e}",
                "error": str(e),
            })

    if not all_docs:
        return {"status": "no_content", "ingested": 0, "documents": doc_metadata_list}

    # Chunk
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    nodes = splitter.get_nodes_from_documents(all_docs)
    logger.info("Total nodes after chunking: %d", len(nodes))

    # Embed + store in ChromaDB
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = f"tenant_{tenant_id}"
    chroma_collection = chroma_client.get_or_create_collection(collection_name)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    VectorStoreIndex(
        nodes=nodes,
        embed_model=embed_model,
        storage_context=storage_context,
        show_progress=True,
    )

    logger.info(
        "Ingestion complete: %d documents, %d nodes → collection '%s'",
        len(pdf_paths),
        len(nodes),
        collection_name,
    )

    return {
        "status": "ok",
        "ingested": len(pdf_paths),
        "total_nodes": len(nodes),
        "collection": collection_name,
        "documents": doc_metadata_list,
    }
