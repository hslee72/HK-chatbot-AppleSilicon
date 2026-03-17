"""RAG query engine with citation support."""

import logging

import chromadb

from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import CitationQueryEngine
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

from server.config import (
    CHROMA_DIR,
    OLLAMA_BASE_URL,
    LLM_MODEL,
    EMBED_MODEL,
    SIMILARITY_TOP_K,
    CITATION_CHUNK_SIZE,
    REGULATION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class RegulationRAGEngine:
    """Per-tenant RAG engine backed by ChromaDB + Ollama."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.collection_name = f"tenant_{tenant_id}"

        self.llm = Ollama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
            request_timeout=120.0,
            system_prompt=REGULATION_SYSTEM_PROMPT,
        )
        self.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

    def _get_index(self) -> VectorStoreIndex:
        """Load the tenant's vector store index."""
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        chroma_collection = chroma_client.get_or_create_collection(self.collection_name)

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
        )

    def query(self, question: str, history: list[dict] | None = None) -> dict:
        """
        Query the RAG pipeline and return answer with citations.

        Returns:
            {
                "answer": str,
                "citations": [{"source": str, "page": int, "text": str}]
            }
        """
        index = self._get_index()

        query_engine = CitationQueryEngine.from_args(
            index,
            llm=self.llm,
            similarity_top_k=SIMILARITY_TOP_K,
            citation_chunk_size=CITATION_CHUNK_SIZE,
        )

        # Build context-aware query with history
        full_query = question
        if history:
            context_parts = []
            for msg in history[-6:]:  # last 3 turns
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context_parts.append(f"{role}: {content}")
            context_parts.append(f"user: {question}")
            full_query = "\n".join(context_parts)

        response = query_engine.query(full_query)

        # Extract citations from source nodes
        citations = []
        seen = set()
        for node in response.source_nodes:
            meta = node.node.metadata
            source = meta.get("source", "unknown")
            page = meta.get("page", 0)
            text = node.node.get_content()[:300]
            key = (source, page)
            if key not in seen:
                seen.add(key)
                citations.append({
                    "source": source,
                    "page": page,
                    "text": text,
                    "score": round(node.score, 4) if node.score else None,
                })

        return {
            "answer": str(response),
            "citations": citations,
        }

    def has_documents(self) -> bool:
        """Check if this tenant has any indexed documents."""
        try:
            chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            collection = chroma_client.get_or_create_collection(self.collection_name)
            return collection.count() > 0
        except Exception:
            return False
