from __future__ import annotations

import mimetypes
from pathlib import Path

from app.schemas import DocumentMetadata, NormalizedDocument


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}


class ValidationError(ValueError):
    pass


def validate_upload(filename: str, content_type: str, size_bytes: int, max_bytes: int) -> None:
    suffix = Path(filename).suffix.lower()
    guessed_type = mimetypes.guess_type(filename)[0]
    effective_type = content_type or guessed_type or ""
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValidationError("Only PDF, PNG, JPG, and JPEG files are supported")
    if effective_type not in ALLOWED_CONTENT_TYPES and content_type:
        raise ValidationError(f"Unsupported content type: {content_type}")
    if size_bytes <= 0:
        raise ValidationError("Uploaded file is empty")
    if size_bytes > max_bytes:
        raise ValidationError("Uploaded file exceeds the configured size limit")


def normalize_document(
    document_id: str,
    filename: str,
    content_type: str,
    size_bytes: int,
    storage_uri: str,
    file_bytes: bytes,
) -> NormalizedDocument:
    suffix = Path(filename).suffix.lower()
    warnings: list[str] = []
    pages: list[str] = []
    text = ""

    if suffix == ".pdf":
        text, pages, warnings = _extract_pdf_text(file_bytes)
    else:
        warnings.append(
            "Image OCR is not configured locally; install an OCR provider or use the LLM/layout pipeline."
        )

    metadata = DocumentMetadata(
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        page_count=max(len(pages), 1 if suffix != ".pdf" else 0),
        storage_uri=storage_uri,
        warnings=warnings,
    )
    return NormalizedDocument(metadata=metadata, text=text, pages=pages)


def _extract_pdf_text(file_bytes: bytes) -> tuple[str, list[str], list[str]]:
    warnings: list[str] = []
    try:
        import fitz
    except ImportError:
        return "", [], ["PyMuPDF is not installed; PDF text extraction was skipped."]

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        return "", [], ["The PDF could not be parsed."]

    pages = []
    for page in document:
        page_text = page.get_text("text").strip()
        pages.append(page_text)
    text = "\n\n".join(part for part in pages if part)
    if not text:
        warnings.append("No digital text was found; scanned PDF OCR/LayoutLM processing is required.")
    return text, pages, warnings

