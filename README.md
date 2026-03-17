# HK-chatbot2

**Regulation RAG Multi-Tenant Chatbot** — AI-powered chatbot for corporate regulation documents with citation-based answers.

[한국어 문서 (Korean)](./README.ko.md)

---

## Overview

HK-chatbot2 is a Retrieval-Augmented Generation (RAG) chatbot designed for querying corporate regulation PDFs. It provides accurate, citation-backed answers by searching through indexed documents and generating responses grounded in the source material.

### Key Features

- **Smart PDF Parsing** — Multi-strategy parser: text extraction → OCR fallback → table detection → VLM image description
- **RAG with Citations** — Every answer includes source references `[REF: document p.page]`
- **Multi-Tenant** — Isolated vector stores per tenant for different departments or organizations
- **OCR Support** — Scanned PDFs parsed via RapidOCR (Korean + English, ONNX-based, no GPU required)
- **Table Extraction** — Tables detected and preserved as structured markdown via pdfplumber
- **VLM Integration** — Charts and figures described by Vision-Language Model (Ollama cloud)
- **Docker/Colima Ready** — Single-command deployment, optimized for low-resource environments

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Docker Container                                   │
│  ┌──────────────┐  ┌────────────────────────────┐   │
│  │ React SPA    │  │ FastAPI Backend             │   │
│  │ (Vite+TW)   │  │                             │   │
│  │              │  │  ┌─────────┐ ┌───────────┐  │   │
│  │ /chat        │◄─┤  │ RAG     │ │ Smart PDF │  │   │
│  │ /documents   │  │  │ Engine  │ │ Parser    │  │   │
│  │              │  │  │(LlamaIdx)│ │(OCR/VLM) │  │   │
│  └──────────────┘  │  └────┬────┘ └───────────┘  │   │
│                    │       │                      │   │
│                    │  ┌────▼────┐  ┌───────────┐  │   │
│                    │  │ChromaDB │  │ HuggingFace│  │   │
│                    │  │(Vector) │  │ Embedding  │  │   │
│                    │  └─────────┘  └───────────┘  │   │
│                    └────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          │
                     ┌────▼─────┐
                     │  Ollama  │  (Host machine)
                     │  LLM/VLM │
                     └──────────┘
```

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **Backend** | FastAPI + LlamaIndex + CitationQueryEngine |
| **Vector Store** | ChromaDB (persistent, per-tenant collections) |
| **Embeddings** | HuggingFace `intfloat/multilingual-e5-small` (in-container) |
| **LLM** | Ollama (cloud or local models) |
| **PDF Parsing** | pypdf + pdfplumber + RapidOCR + Ollama VLM |
| **Deployment** | Docker Compose (Colima compatible) |

---

## Prerequisites

- **Docker** (via [Colima](https://github.com/abiosoft/colima) or Docker Desktop)
- **Ollama** running on host machine
  ```bash
  ollama pull nemotron-3-super:cloud
  ```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/biztalk72/HK-chatbot2.git
cd HK-chatbot2

# 2. Place PDF files in data/
cp /path/to/your/regulations/*.pdf data/

# 3. Build & run
docker compose up --build -d

# 4. Open browser
open http://localhost:8000
```

### Index Documents

After startup, index your PDF documents:

```bash
# Index all PDFs (OCR enabled by default)
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id": "default"}'

# Index with VLM for image/chart descriptions
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"use_ocr": true, "use_vlm": true}'

# Index specific files only
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"filenames": ["regulation_A.pdf", "regulation_B.pdf"]}'
```

Or use the web UI: navigate to `/documents` and click **"전체 인덱싱 시작"**.

---

## Usage

1. **Documents** (`/documents`) — View indexed documents (title, summary, page count), trigger indexing
2. **Chat** (`/chat`) — Ask questions about regulations, get citation-backed answers

### Chat Example

```
Q: 개인정보 처리에 관한 규정은?
A: 개인정보 처리에 관하여... [REF: 개인정보보호규정.pdf p.5]
```

---

## Smart PDF Parser

The parser automatically selects the best strategy per page:

| Strategy | Trigger | Tool |
|----------|---------|------|
| **Text** | Standard digital PDF | pypdf |
| **OCR** | Scanned pages (< 50 chars extracted) | RapidOCR (ONNX) |
| **Table** | Tables detected on page | pdfplumber → markdown |
| **VLM** | Images/charts detected + VLM enabled | Ollama vision model |

Each parsed page includes metadata: `parse_method`, `parse_quality`, `has_tables`, `has_images`.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | System status + Ollama connection |
| `GET` | `/api/tenants` | List all tenants |
| `POST` | `/api/tenants` | Create a new tenant |
| `GET` | `/api/documents?tenant_id=X` | List indexed docs (title, summary, pages) |
| `GET` | `/api/ingest/files` | List available PDFs in `data/` |
| `POST` | `/api/ingest` | Ingest PDFs (chunking + vectorizing) |
| `POST` | `/api/chat` | RAG query with citation-backed answer |

### POST `/api/ingest`

```json
{
  "tenant_id": "default",
  "filenames": null,
  "use_ocr": true,
  "use_vlm": false
}
```

### POST `/api/chat`

```json
{
  "tenant_id": "default",
  "question": "연차휴가 규정은?",
  "history": []
}
```

---

## Project Structure

```
HK-chatbot2/
├── data/                    # PDF documents (mounted read-only)
├── server/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # All configuration & env vars
│   ├── requirements.txt     # Python dependencies
│   ├── rag/
│   │   ├── parsers.py       # Smart PDF parser (text/OCR/table/VLM)
│   │   ├── ingestion.py     # PDF → chunk → embed → ChromaDB pipeline
│   │   └── engine.py        # RAG query engine with citations
│   ├── routers/
│   │   ├── chat.py          # POST /api/chat
│   │   ├── documents.py     # GET  /api/documents
│   │   ├── ingest.py        # POST /api/ingest
│   │   ├── health.py        # GET  /api/health
│   │   └── tenants.py       # Tenant CRUD
│   └── tenants/
│       └── manager.py       # JSON-based tenant management
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # Router (Chat / Documents)
│   │   ├── screens/
│   │   │   ├── Chat.tsx      # Chat interface
│   │   │   └── Documents.tsx # Document list + indexing
│   │   └── components/
│   │       └── CitationBubble.tsx
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile               # Multi-stage build (Node + Python)
├── docker-compose.yml
├── CHANGELOG.md
├── README.md                # English documentation
└── README.ko.md             # Korean documentation
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama server URL |
| `LLM_MODEL` | `qwen2.5:7b` | LLM for answer generation |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | HuggingFace embedding model |
| `VLM_MODEL` | `glm-5:cloud` | Vision-Language model for images |
| `OCR_ENABLED` | `true` | Enable OCR fallback for scanned PDFs |
| `VLM_ENABLED` | `false` | Enable VLM for image/chart descriptions |
| `CHUNK_SIZE` | `512` | Text chunk size (tokens) |
| `CHUNK_OVERLAP` | `64` | Chunk overlap (tokens) |
| `SIMILARITY_TOP_K` | `5` | Top-K chunks retrieved per query |
| `CITATION_CHUNK_SIZE` | `256` | Citation chunk size |

---

## Local Development

```bash
# Backend
cd server
pip install -r requirements.txt
OLLAMA_BASE_URL=http://localhost:11434 \
  uvicorn server.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Deployment Notes

### Colima (recommended for macOS)

```bash
colima start --cpu 2 --memory 4
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
docker compose up --build -d
```

> **Note**: With 2GB RAM, index PDFs in small batches (2–5 files) to avoid OOM.

### Production Considerations

- Mount `data/` as read-only (`:ro`) — already configured
- Named volumes for `chroma_db` and `tenants_store` persistence
- Configure specific CORS origins instead of `*`
- Consider adding authentication (Phase 3)

---

## Roadmap

- [x] **Phase 1** — RAG pipeline with citation support
- [x] **Phase 1.5** — OCR + VLM smart PDF parsing
- [ ] **Phase 2** — QA log collection → LoRA fine-tuning
- [ ] **Phase 3** — Auth/RBAC, per-tenant prompts, admin dashboard

---

## License

MIT
