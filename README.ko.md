# HK-chatbot2

**규정 RAG 멀티테넌트 챗봇** — 기업 규정 문서 기반 AI 챗봇, 출처 인용 답변 지원

[English Documentation](./README.md)

---

## 개요

HK-chatbot2는 기업 규정 PDF를 대상으로 한 RAG(Retrieval-Augmented Generation) 챗봇입니다. 인덱싱된 문서를 검색하고, 원문 근거에 기반한 정확한 인용 답변을 제공합니다.

### 주요 기능

- **스마트 PDF 파싱** — 멀티 전략 파서: 텍스트 추출 → OCR 폴백 → 표 감지 → VLM 이미지 설명
- **출처 인용 답변** — 모든 답변에 출처 참조 포함 `[REF: 문서명 p.페이지]`
- **멀티테넌트** — 부서/조직별 독립된 벡터 스토어
- **OCR 지원** — RapidOCR로 스캔 PDF 처리 (한국어+영어, ONNX 기반, GPU 불필요)
- **표 추출** — pdfplumber로 표 감지 후 마크다운 구조화
- **VLM 연동** — Ollama 비전 모델로 차트/도표 텍스트 설명 생성
- **Docker/Colima 배포** — 단일 명령 배포, 저사양 환경 최적화
- **한글 IME 지원** — 채팅 입력 시 한글 조합 중 Enter 전송 문제 해결
- **흥국생명 CI** — 공식 기업 favicon 적용

---

## 아키텍처

```
┌─────────────────────────────────────────────────────┐
│  Docker 컨테이너                                      │
│  ┌──────────────┐  ┌────────────────────────────┐   │
│  │ React SPA    │  │ FastAPI 백엔드              │   │
│  │ (Vite+TW)   │  │                             │   │
│  │              │  │  ┌─────────┐ ┌───────────┐  │   │
│  │ /chat        │◄─┤  │ RAG     │ │ 스마트 PDF │  │   │
│  │ /documents   │  │  │ 엔진    │ │ 파서       │  │   │
│  │              │  │  │(LlamaIdx)│ │(OCR/VLM) │  │   │
│  └──────────────┘  │  └────┬────┘ └───────────┘  │   │
│                    │       │                      │   │
│                    │  ┌────▼────┐  ┌───────────┐  │   │
│                    │  │ChromaDB │  │ HuggingFace│  │   │
│                    │  │(벡터DB) │  │ 임베딩     │  │   │
│                    │  └─────────┘  └───────────┘  │   │
│                    └────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                          │
                     ┌────▼─────┐
                     │  Ollama  │  (호스트 머신)
                     │  LLM/VLM │
                     └──────────┘
```

| 계층 | 기술 |
|------|------|
| **프론트엔드** | React 18 + Vite + Tailwind CSS |
| **백엔드** | FastAPI + LlamaIndex + CitationQueryEngine |
| **벡터 스토어** | ChromaDB (영구 저장, 테넌트별 컬렉션) |
| **임베딩** | HuggingFace `intfloat/multilingual-e5-small` (컨테이너 내부) |
| **LLM** | Ollama (클라우드 또는 로컬 모델) |
| **PDF 파싱** | pypdf + pdfplumber + RapidOCR + Ollama VLM |
| **배포** | Docker Compose (Colima 호환) |

---

## 사전 요구사항

- **Docker** ([Colima](https://github.com/abiosoft/colima) 또는 Docker Desktop)
- **Ollama** (호스트 머신에서 실행)
  ```bash
  ollama pull nemotron-3-super:cloud
  ```

---

## 빠른 시작

```bash
# 1. 클론
git clone https://github.com/biztalk72/HK-chatbot2.git
cd HK-chatbot2

# 2. PDF 파일을 data/ 디렉토리에 배치
cp /path/to/your/regulations/*.pdf data/

# 3. 빌드 + 실행
docker compose up --build -d

# 4. 브라우저에서 접속
open http://localhost:8000
```

### 문서 인덱싱

서버 시작 후 PDF 문서를 인덱싱합니다:

```bash
# 전체 PDF 인덱싱 (OCR 기본 활성화)
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"tenant_id": "default"}'

# VLM 포함 인덱싱 (이미지/도표 설명 추가)
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"use_ocr": true, "use_vlm": true}'

# 특정 파일만 인덱싱
curl -X POST http://localhost:8000/api/ingest \
  -H 'Content-Type: application/json' \
  -d '{"filenames": ["규정_A.pdf", "규정_B.pdf"]}'
```

또는 웹 UI에서: `/documents` 페이지 → **"전체 인덱싱 시작"** 클릭

---

## 사용 방법

1. **문서 관리** (`/documents`) — 인덱싱된 문서 목록 확인 (제목/요약/페이지수), 인덱싱 실행
2. **채팅** (`/chat`) — 규정 질문, 출처 인용 답변 수신

### 채팅 예시

```
Q: 개인정보 처리에 관한 규정은?
A: 개인정보 처리에 관하여... [REF: 개인정보보호규정.pdf p.5]

Q: 연차휴가 신청 절차는?
A: 연차휴가 신청은... [REF: 인사규정.pdf p.12]
```

---

## 스마트 PDF 파서

페이지별로 최적의 파싱 전략을 자동 선택합니다:

| 전략 | 트리거 조건 | 도구 |
|------|-------------|------|
| **텍스트** | 일반 디지털 PDF | pypdf |
| **OCR** | 스캔 페이지 (추출 텍스트 < 50자) | RapidOCR (ONNX) |
| **표** | 페이지에서 표 감지 | pdfplumber → 마크다운 |
| **VLM** | 이미지/도표 감지 + VLM 활성화 | Ollama 비전 모델 |

각 페이지에 메타데이터 포함: `parse_method`, `parse_quality`, `has_tables`, `has_images`

---

## API 레퍼런스

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/health` | 시스템 상태 + Ollama 연결 확인 |
| `GET` | `/api/tenants` | 테넌트 목록 조회 |
| `POST` | `/api/tenants` | 테넌트 생성 |
| `GET` | `/api/documents?tenant_id=X` | 인덱싱된 문서 목록 (제목/요약/페이지수) |
| `GET` | `/api/ingest/files` | data/ 내 사용 가능 PDF 파일 목록 |
| `POST` | `/api/ingest` | PDF 인제스트 (청킹 + 벡터화) |
| `POST` | `/api/chat` | RAG 질의 + 인용 포함 답변 |

### POST `/api/ingest` 요청 본문

```json
{
  "tenant_id": "default",
  "filenames": null,
  "use_ocr": true,
  "use_vlm": false
}
```

### POST `/api/chat` 요청 본문

```json
{
  "tenant_id": "default",
  "question": "연차휴가 규정은?",
  "history": []
}
```

---

## 프로젝트 구조

```
HK-chatbot2/
├── data/                    # PDF 문서 (읽기 전용 마운트)
├── server/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── config.py            # 전체 설정 및 환경변수
│   ├── requirements.txt     # Python 의존성
│   ├── rag/
│   │   ├── parsers.py       # 스마트 PDF 파서 (텍스트/OCR/표/VLM)
│   │   ├── ingestion.py     # PDF → 청킹 → 임베딩 → ChromaDB 파이프라인
│   │   └── engine.py        # RAG 쿼리 엔진 (인용 지원)
│   ├── routers/
│   │   ├── chat.py          # POST /api/chat
│   │   ├── documents.py     # GET  /api/documents
│   │   ├── ingest.py        # POST /api/ingest
│   │   ├── health.py        # GET  /api/health
│   │   └── tenants.py       # 테넌트 CRUD
│   └── tenants/
│       └── manager.py       # JSON 기반 테넌트 관리
├── frontend/
│   ├── src/
│   │   ├── App.tsx           # 라우터 (Chat / Documents)
│   │   ├── screens/
│   │   │   ├── Chat.tsx      # 채팅 인터페이스
│   │   │   └── Documents.tsx # 문서 목록 + 인덱싱
│   │   └── components/
│   │       └── CitationBubble.tsx
│   ├── package.json
│   └── vite.config.ts
├── Dockerfile               # 멀티스테이지 빌드 (Node + Python)
├── docker-compose.yml
├── CHANGELOG.md
├── README.md                # 영문 문서
└── README.ko.md             # 한국어 문서
```

---

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Ollama 서버 URL |
| `LLM_MODEL` | `qwen2.5:7b` | 답변 생성 LLM 모델 |
| `EMBED_MODEL` | `intfloat/multilingual-e5-large` | HuggingFace 임베딩 모델 |
| `VLM_MODEL` | `glm-5:cloud` | 이미지 설명용 비전 모델 |
| `OCR_ENABLED` | `true` | 스캔 PDF용 OCR 폴백 활성화 |
| `VLM_ENABLED` | `false` | 이미지/도표 VLM 설명 활성화 |
| `CHUNK_SIZE` | `512` | 텍스트 청크 크기 (토큰) |
| `CHUNK_OVERLAP` | `64` | 청크 오버랩 (토큰) |
| `SIMILARITY_TOP_K` | `5` | 쿼리당 검색 상위 K개 |
| `CITATION_CHUNK_SIZE` | `256` | 인용 청크 크기 |

---

## 로컬 개발 (Docker 없이)

```bash
# 백엔드
cd server
pip install -r requirements.txt
OLLAMA_BASE_URL=http://localhost:11434 \
  uvicorn server.main:app --reload --port 8000

# 프론트엔드 (별도 터미널)
cd frontend
npm install
npm run dev
```

---

## 배포 가이드

### Colima (macOS 권장)

```bash
colima start --cpu 2 --memory 4
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
docker compose up --build -d
```

> **참고**: RAM 2GB 환경에서는 PDF를 소규모 배치(2~5개)로 나눠 인덱싱하세요 (OOM 방지).

### 운영 환경 고려사항

- `data/` 읽기 전용 마운트 (`:ro`) — 이미 설정됨
- `chroma_db`, `tenants_store`는 네임드 볼륨으로 영구 보존
- CORS origin을 `*` 대신 특정 도메인으로 제한
- 인증/인가 추가 (Phase 3에서 구현 예정)

---

## 로드맵

- [x] **Phase 1** — RAG 파이프라인 + 출처 인용 답변
- [x] **Phase 1.5** — OCR + VLM 스마트 PDF 파싱
- [x] **Phase 1.6** — 흥국생명 CI favicon, 한글 IME 수정, 이중언어 문서
- [ ] **Phase 2** — QA 로그 수집 → LoRA 파인튜닝 (도메인 스타일/추론 패턴)
- [ ] **Phase 3** — Auth/RBAC, 테넌트별 프롬프트 커스터마이즈, 관리자 대시보드

---

## 라이선스

MIT
