"""Smart PDF parsing with multiple strategies: text, OCR, table, VLM."""

import base64
import io
import logging
from pathlib import Path

import httpx
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
from pypdf import PdfReader

from server.config import OLLAMA_BASE_URL, VLM_MODEL

logger = logging.getLogger(__name__)

# Lazy-loaded OCR engine (heavy import)
_ocr_engine = None


def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr_engine = RapidOCR()
    return _ocr_engine


# ─── Page quality detection ──────────────────────────────────────────────────

MIN_TEXT_CHARS = 50  # below this, page is considered scanned/image


def _assess_page(text: str | None) -> str:
    """Classify page as 'text', 'poor', or 'empty'."""
    if not text or not text.strip():
        return "empty"
    stripped = text.strip()
    if len(stripped) < MIN_TEXT_CHARS:
        return "poor"
    return "text"


def _has_tables(plumber_page) -> bool:
    """Detect if a pdfplumber page contains tables."""
    tables = plumber_page.find_tables()
    return len(tables) > 0


def _has_images(pypdf_page) -> bool:
    """Detect if a pypdf page contains embedded images."""
    try:
        xobjects = pypdf_page.get("/Resources", {}).get("/XObject", {})
        if hasattr(xobjects, "get_object"):
            xobjects = xobjects.get_object()
        for obj_name in xobjects:
            obj = xobjects[obj_name]
            if hasattr(obj, "get_object"):
                obj = obj.get_object()
            subtype = obj.get("/Subtype", "")
            if subtype == "/Image":
                return True
    except Exception:
        pass
    return False


# ─── Text extraction (existing, fast) ────────────────────────────────────────

def extract_text(pypdf_page) -> str:
    """Standard pypdf text extraction."""
    return pypdf_page.extract_text() or ""


# ─── OCR extraction ──────────────────────────────────────────────────────────

def extract_ocr(pdf_path: Path, page_num: int, dpi: int = 200) -> str:
    """
    Render a single PDF page to image and run OCR.
    page_num is 1-indexed.
    """
    try:
        images = convert_from_path(
            str(pdf_path),
            first_page=page_num,
            last_page=page_num,
            dpi=dpi,
        )
        if not images:
            return ""

        img = images[0]
        import numpy as np
        img_array = np.array(img)

        engine = _get_ocr_engine()
        result, _ = engine(img_array)

        if not result:
            return ""

        # result is list of (bbox, text, confidence)
        lines = [item[1] for item in result]
        return "\n".join(lines)
    except Exception as e:
        logger.warning("OCR failed for %s p.%d: %s", pdf_path.name, page_num, e)
        return ""


# ─── Table extraction ────────────────────────────────────────────────────────

def extract_tables(plumber_page) -> str:
    """Extract tables from a pdfplumber page as markdown."""
    tables = plumber_page.extract_tables()
    if not tables:
        return ""

    parts = []
    for table in tables:
        if not table or not table[0]:
            continue
        # Build markdown table
        md_lines = []
        headers = [str(c or "").strip() for c in table[0]]
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in table[1:]:
            cells = [str(c or "").strip() for c in row]
            # Pad if row has fewer cells
            while len(cells) < len(headers):
                cells.append("")
            md_lines.append("| " + " | ".join(cells[:len(headers)]) + " |")
        parts.append("\n".join(md_lines))

    return "\n\n".join(parts)


# ─── VLM description ─────────────────────────────────────────────────────────

def describe_with_vlm(pdf_path: Path, page_num: int, dpi: int = 150) -> str:
    """
    Render page to image and send to Ollama VLM for description.
    Returns description text or empty string if VLM unavailable.
    """
    try:
        images = convert_from_path(
            str(pdf_path),
            first_page=page_num,
            last_page=page_num,
            dpi=dpi,
        )
        if not images:
            return ""

        img = images[0]
        # Resize for efficiency (max 1024px wide)
        if img.width > 1024:
            ratio = 1024 / img.width
            img = img.resize((1024, int(img.height * ratio)), Image.LANCZOS)

        # Encode to base64
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        # Call Ollama vision API
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": VLM_MODEL,
                "prompt": (
                    "이 문서 페이지의 내용을 상세히 설명해 주세요. "
                    "표, 그래프, 다이어그램이 있다면 그 내용과 데이터를 텍스트로 정리해 주세요. "
                    "한국어로 답변하세요."
                ),
                "images": [img_b64],
                "stream": False,
            },
            timeout=120.0,
        )

        if resp.status_code == 200:
            data = resp.json()
            return data.get("response", "")
        else:
            logger.warning("VLM returned %d for %s p.%d", resp.status_code, pdf_path.name, page_num)
            return ""
    except Exception as e:
        logger.warning("VLM failed for %s p.%d: %s", pdf_path.name, page_num, e)
        return ""


# ─── Smart page parser ───────────────────────────────────────────────────────

def parse_page(
    pdf_path: Path,
    pypdf_page,
    plumber_page,
    page_num: int,
    use_ocr: bool = True,
    use_vlm: bool = False,
) -> dict:
    """
    Parse a single PDF page using the best available strategy.

    Returns:
        {
            "text": str,
            "method": str,        # "text", "ocr", "text+table", "ocr+table", "vlm", etc.
            "quality": float,     # 0.0-1.0 estimated text quality
            "has_tables": bool,
            "has_images": bool,
        }
    """
    # Step 1: Try standard text extraction
    raw_text = extract_text(pypdf_page)
    quality_type = _assess_page(raw_text)
    method_parts = []
    parts = []

    # Step 2: Text or OCR
    if quality_type == "text":
        parts.append(raw_text)
        method_parts.append("text")
    elif use_ocr and quality_type in ("empty", "poor"):
        ocr_text = extract_ocr(pdf_path, page_num)
        if ocr_text.strip():
            parts.append(ocr_text)
            method_parts.append("ocr")
        elif raw_text.strip():
            # OCR failed too, use whatever pypdf got
            parts.append(raw_text)
            method_parts.append("text-fallback")
    elif raw_text.strip():
        parts.append(raw_text)
        method_parts.append("text-fallback")

    # Step 3: Table extraction
    tables_detected = _has_tables(plumber_page)
    if tables_detected:
        table_md = extract_tables(plumber_page)
        if table_md.strip():
            parts.append(f"\n[표 데이터]\n{table_md}")
            method_parts.append("table")

    # Step 4: VLM for images/figures
    images_detected = _has_images(pypdf_page)
    vlm_text = ""
    if use_vlm and images_detected:
        vlm_text = describe_with_vlm(pdf_path, page_num)
        if vlm_text.strip():
            parts.append(f"\n[이미지/도표 설명]\n{vlm_text}")
            method_parts.append("vlm")

    final_text = "\n\n".join(parts).strip()
    quality = min(1.0, len(final_text) / 500) if final_text else 0.0

    return {
        "text": final_text,
        "method": "+".join(method_parts) if method_parts else "empty",
        "quality": round(quality, 2),
        "has_tables": tables_detected,
        "has_images": images_detected,
    }


# ─── Full document parser ────────────────────────────────────────────────────

def parse_pdf(
    pdf_path: Path,
    use_ocr: bool = True,
    use_vlm: bool = False,
) -> list[dict]:
    """
    Parse all pages of a PDF using smart multi-strategy approach.

    Returns list of dicts per page:
        [{"text", "method", "quality", "page", "has_tables", "has_images"}, ...]
    """
    pypdf_reader = PdfReader(str(pdf_path))
    plumber_doc = pdfplumber.open(str(pdf_path))

    results = []
    total_pages = len(pypdf_reader.pages)

    for idx in range(total_pages):
        page_num = idx + 1
        pypdf_page = pypdf_reader.pages[idx]
        plumber_page = plumber_doc.pages[idx] if idx < len(plumber_doc.pages) else None

        if plumber_page:
            page_result = parse_page(
                pdf_path, pypdf_page, plumber_page, page_num,
                use_ocr=use_ocr, use_vlm=use_vlm,
            )
        else:
            # Fallback: just text extraction
            text = extract_text(pypdf_page)
            page_result = {
                "text": text,
                "method": "text",
                "quality": min(1.0, len(text) / 500) if text else 0.0,
                "has_tables": False,
                "has_images": False,
            }

        page_result["page"] = page_num
        results.append(page_result)

    plumber_doc.close()
    return results
