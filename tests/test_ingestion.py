from __future__ import annotations

import pytest

from app.ingestion import ValidationError, validate_upload


def test_validate_upload_accepts_pdf() -> None:
    validate_upload("application.pdf", "application/pdf", 10, 1024)


def test_validate_upload_rejects_unsupported_extension() -> None:
    with pytest.raises(ValidationError):
        validate_upload("notes.txt", "text/plain", 10, 1024)


def test_validate_upload_rejects_large_file() -> None:
    with pytest.raises(ValidationError):
        validate_upload("application.pdf", "application/pdf", 2048, 1024)

