from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
    result_dir: Path = Path(os.getenv("RESULT_DIR", "data/results"))

    storage_backend: str = os.getenv("STORAGE_BACKEND", "local").lower()
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")

    llm_provider: str = os.getenv("LLM_PROVIDER", "offline").lower()
    llm_model: str = os.getenv("LLM_MODEL", "")

    layoutlm_enabled: bool = _bool("LAYOUTLM_ENABLED", False)
    layoutlm_model: str = os.getenv("LAYOUTLM_MODEL", "microsoft/layoutlmv3-base")

    risk_model_path: Path = Path(os.getenv("RISK_MODEL_PATH", "models/risk_classifier.pt"))

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()

