"""
Document loader - extracts raw text from PDF, DOCX, TXT, CSV files.
"""
import os
import csv
import io
from pathlib import Path
from typing import Tuple
import pypdf
import docx
from app.core.logging import logger


async def extract_text(file_path: str, file_type: str) -> Tuple[str, dict]:
    """
    Returns (raw_text, metadata).
    metadata contains page_count, word_count, etc.
    """
    file_type = file_type.lower().lstrip(".")
    path = Path(file_path)

    if file_type == "pdf":
        return await _load_pdf(path)
    elif file_type in ("docx", "doc"):
        return await _load_docx(path)
    elif file_type == "txt":
        return await _load_txt(path)
    elif file_type == "csv":
        return await _load_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


async def _load_pdf(path: Path) -> Tuple[str, dict]:
    texts = []
    try:
        reader = pypdf.PdfReader(str(path))
        page_count = len(reader.pages)
        for page in reader.pages:
            text = page.extract_text() or ""
            texts.append(text)
        full_text = "\n\n".join(texts)
        return full_text, {"page_count": page_count, "word_count": len(full_text.split())}
    except Exception as e:
        logger.error("PDF extraction error", path=str(path), error=str(e))
        raise


async def _load_docx(path: Path) -> Tuple[str, dict]:
    try:
        doc = docx.Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n\n".join(paragraphs)
        return full_text, {"paragraph_count": len(paragraphs), "word_count": len(full_text.split())}
    except Exception as e:
        logger.error("DOCX extraction error", path=str(path), error=str(e))
        raise


async def _load_txt(path: Path) -> Tuple[str, dict]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        return text, {"word_count": len(text.split()), "char_count": len(text)}
    except Exception as e:
        logger.error("TXT loading error", path=str(path), error=str(e))
        raise


async def _load_csv(path: Path) -> Tuple[str, dict]:
    try:
        rows = []
        with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                row_text = " | ".join(f"{k}: {v}" for k, v in row.items() if v)
                rows.append(row_text)
        full_text = "\n".join(rows)
        return full_text, {"row_count": len(rows), "columns": headers}
    except Exception as e:
        logger.error("CSV loading error", path=str(path), error=str(e))
        raise
