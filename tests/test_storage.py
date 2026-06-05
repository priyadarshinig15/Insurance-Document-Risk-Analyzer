from __future__ import annotations

from app.config import Settings
from app.storage import LocalStorage


def test_local_storage_round_trip(tmp_path) -> None:
    settings = Settings(upload_dir=tmp_path / "uploads", result_dir=tmp_path / "results")
    storage = LocalStorage(settings)

    upload_uri = storage.save_upload("doc-1", "sample.pdf", b"hello")
    result_uri = storage.save_result("doc-1", {"document_id": "doc-1", "risk_score": 10})

    assert upload_uri.endswith("doc-1-sample.pdf")
    assert result_uri.endswith("doc-1.json")
    assert storage.get_result("doc-1")["risk_score"] == 10
    assert storage.ready()

