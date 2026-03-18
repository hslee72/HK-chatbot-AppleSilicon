# Changelog

All notable changes to this project will be documented in this file.

## [0.2.1] - 2026-03-18

### Added
- Heungkuk Life Insurance official CI favicon (`frontend/public/favicon.ico`)
- Korean IME (hangul) composition handling — prevents last character from being left behind on Enter

### Changed
- Updated `README.md` (English) and `README.ko.md` (Korean) with latest features
- Updated `CHANGELOG.md` with v0.2.1 release

## [0.2.0] - 2026-03-17

### Added
- **Smart PDF Parser** (`server/rag/parsers.py`)
  - Multi-strategy parsing: text → OCR → table → VLM
  - RapidOCR (ONNX) for scanned PDF pages (Korean + English)
  - pdfplumber table detection → markdown conversion
  - Ollama VLM cloud model for image/chart descriptions
  - Per-page metadata: `parse_method`, `parse_quality`, `has_tables`, `has_images`
- OCR/VLM configuration: `VLM_MODEL`, `OCR_ENABLED`, `VLM_ENABLED` environment variables
- `use_ocr` and `use_vlm` options in ingestion API
- `poppler-utils` system dependency in Docker image
- New dependencies: `rapidocr-onnxruntime`, `pdfplumber`, `pdf2image`, `Pillow`, `numpy`
- Bilingual documentation: `README.md` (English) + `README.ko.md` (Korean)
- `CHANGELOG.md`

### Changed
- `ingestion.py`: Replaced simple pypdf extraction with smart multi-strategy parser
- Document metadata now includes parsing method and quality score
- Updated `README.md` with comprehensive project documentation

## [0.1.0] - 2026-03-16

### Added
- Initial release: Regulation RAG Multi-Tenant Chatbot
- **Backend**: FastAPI + LlamaIndex + ChromaDB
  - CitationQueryEngine for source-referenced answers
  - Multi-tenant vector store (per-tenant ChromaDB collections)
  - PDF ingestion pipeline: parse → chunk → embed → store
  - Tenant CRUD (JSON-based storage)
  - Health check with Ollama connectivity status
- **Frontend**: React + Vite + Tailwind CSS
  - Chat screen with citation display
  - Documents screen with title/summary/page listing
  - SPA routing served from FastAPI
- **Embedding**: HuggingFace `intfloat/multilingual-e5-small` (in-container, no Ollama dependency)
- **LLM**: Ollama integration (cloud model support: `nemotron-3-super:cloud`)
- Docker Compose deployment (Colima compatible)
- Korean system prompt for regulation-specific responses
