# HK-chatbot2 — 규정 RAG 멀티테넌트 챗봇

규정 PDF를 대상으로 한 RAG(Retrieval-Augmented Generation) 기반 AI 챗봇.
LlamaIndex + ChromaDB + Ollama 백엔드, React 프론트엔드, Docker/Colima 배포.

---

## 아키텍처

- **Backend**: FastAPI + LlamaIndex + ChromaDB (벡터 스토어)
- **Frontend**: React + Vite + Tailwind CSS
- **LLM**: Ollama (호스트 머신에서 실행)
- **배포**: Docker Compose (Colima 호환)

---

## 사전 요구사항

- **Colima** + **Docker** (이미 설치됨)
- **Ollama** (호스트에서 실행)
  ```bash
  ollama pull llama3.2
  ollama pull nomic-embed-text
  ```

---

## 빠른 시작 (Docker)

```bash
# 1. PDF 파일을 data/ 디렉토리에 배치 (이미 완료)

# 2. 빌드 + 실행
docker compose up --build -d

# 3. 브라우저에서 접속
open http://localhost:8000
```

---

## 사용 방법

1. **문서 관리** (`/documents`) 페이지에서 "전체 인덱싱 시작" 클릭
2. 인덱싱 완료 후 **채팅** (`/chat`) 페이지에서 규정 질문
3. 답변에 출처(REF) 인용이 자동 포함됨

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 시스템 상태 + Ollama 연결 확인 |
| GET | `/api/tenants` | 테넌트 목록 |
| POST | `/api/tenants` | 테넌트 생성 |
| GET | `/api/documents?tenant_id=X` | 인덱싱된 문서 목록 (제목/요약/페이지수) |
| GET | `/api/ingest/files` | data/ 내 사용 가능한 PDF 파일 목록 |
| POST | `/api/ingest` | PDF 인제스트 (chunking + vectorizing) |
| POST | `/api/chat` | RAG 질의 + 인용 포함 답변 |

---

## 로컬 개발 (Docker 없이)

```bash
# Backend
cd server
pip install -r requirements.txt
OLLAMA_BASE_URL=http://localhost:11434 uvicorn server.main:app --reload --port 8000

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev
```

---

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama 서버 주소 |
| `LLM_MODEL` | `llama3.2` | 답변 생성 모델 |
| `EMBED_MODEL` | `nomic-embed-text` | 임베딩 모델 |
| `CHUNK_SIZE` | `512` | 청킹 사이즈 (토큰) |
| `CHUNK_OVERLAP` | `64` | 청크 오버랩 (토큰) |
| `SIMILARITY_TOP_K` | `5` | 검색 상위 K개 |

---

## 향후 계획

- **Phase 2**: QA 로그 수집 → LoRA 파인튜닝 (도메인 스타일/추론 패턴)
- **Phase 3**: Auth/RBAC, 테넌트별 프롬프트 커스터마이즈, 관리자 대시보드
