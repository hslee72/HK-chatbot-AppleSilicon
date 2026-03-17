"""Application configuration."""

import os
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db")))
TENANTS_DIR = Path(os.getenv("TENANTS_DIR", str(BASE_DIR / "tenants_store")))
STATIC_DIR = Path(os.getenv("STATIC_DIR", str(BASE_DIR / "static")))

# ─── Ollama ───────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")

# ─── Embedding (HuggingFace, runs locally — no Ollama dependency) ─────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "intfloat/multilingual-e5-large")

# ─── OCR / VLM ─────────────────────────────────────────────────────────────────
VLM_MODEL = os.getenv("VLM_MODEL", "glm-5:cloud")
OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() == "true"
VLM_ENABLED = os.getenv("VLM_ENABLED", "false").lower() == "true"

# ─── Chunking ─────────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "64"))

# ─── RAG ──────────────────────────────────────────────────────────────────────
SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "5"))
CITATION_CHUNK_SIZE = int(os.getenv("CITATION_CHUNK_SIZE", "256"))

# ─── System prompt ────────────────────────────────────────────────────────────
REGULATION_SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", """당신은 기업 규정 해석 전문 AI 어시스턴트입니다.

규칙:
1. 반드시 제공된 규정 문서의 내용만을 근거로 답변하세요.
2. 답변 시 반드시 출처를 명시하세요: [REF: 문서명 p.페이지번호]
3. 규정에 명시되지 않은 내용은 "해당 규정에서 관련 내용을 찾을 수 없습니다"라고 답변하세요.
4. 여러 규정이 충돌하는 경우, 각 규정의 내용을 모두 인용하고 차이점을 설명하세요.
5. 전문 용어는 규정에서 사용하는 용어를 그대로 사용하세요.
""")
