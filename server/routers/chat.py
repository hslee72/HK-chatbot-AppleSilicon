"""Chat endpoint with RAG query."""

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.rag.engine import RegulationRAGEngine
from server.tenants.manager import get_tenant, ensure_default_tenant

router = APIRouter(tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    tenant_id: str = "default"
    question: str
    history: list[ChatMessage] = []


@router.post("/chat")
async def chat(req: ChatRequest):
    """Query the regulation RAG engine."""
    ensure_default_tenant()

    tenant = get_tenant(req.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    engine = RegulationRAGEngine(req.tenant_id)

    if not engine.has_documents():
        return {
            "answer": "아직 인덱싱된 문서가 없습니다. 먼저 문서를 업로드해 주세요.",
            "citations": [],
        }

    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]

    try:
        result = await asyncio.to_thread(engine.query, req.question, history_dicts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
