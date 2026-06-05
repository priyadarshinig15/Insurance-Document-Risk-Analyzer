from __future__ import annotations

from app.config import Settings
from app.schemas import NormalizedDocument


class LayoutAnalyzer:
    def __init__(self, settings: Settings):
        self.enabled = settings.layoutlm_enabled
        self.model_name = settings.layoutlm_model
        self._ready = False
        self._load_error: str | None = None
        if self.enabled:
            self._ready = self._try_load()

    def _try_load(self) -> bool:
        try:
            from transformers import LayoutLMv3Processor  # noqa: F401
        except Exception as exc:
            self._load_error = str(exc)
            return False
        return True

    def analyze(self, document: NormalizedDocument) -> dict[str, object]:
        text = document.text or ""
        line_count = len([line for line in text.splitlines() if line.strip()])
        token_count = len(text.split())
        features: dict[str, object] = {
            "provider": "layoutlmv3" if self._ready else "fallback-layout-features",
            "model": self.model_name if self.enabled else None,
            "ready": self._ready,
            "page_count": document.metadata.page_count,
            "line_count": line_count,
            "token_count": token_count,
            "has_tables_hint": "|" in text or "\t" in text,
        }
        if self._load_error:
            features["load_error"] = self._load_error
        return features

    def ready(self) -> bool:
        return self._ready or not self.enabled

