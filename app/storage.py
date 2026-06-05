from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.config import Settings


class StorageError(RuntimeError):
    pass


class Storage(ABC):
    @abstractmethod
    def save_upload(self, document_id: str, filename: str, content: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def save_result(self, document_id: str, result: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_result(self, document_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError


class LocalStorage(Storage):
    def __init__(self, settings: Settings):
        self.upload_dir = settings.upload_dir
        self.result_dir = settings.result_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, document_id: str, filename: str, content: bytes) -> str:
        safe_name = Path(filename).name
        target = self.upload_dir / f"{document_id}-{safe_name}"
        target.write_bytes(content)
        return str(target)

    def save_result(self, document_id: str, result: dict[str, Any]) -> str:
        target = self.result_dir / f"{document_id}.json"
        target.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        return str(target)

    def get_result(self, document_id: str) -> dict[str, Any]:
        target = self.result_dir / f"{document_id}.json"
        if not target.exists():
            raise FileNotFoundError(document_id)
        return json.loads(target.read_text(encoding="utf-8"))

    def ready(self) -> bool:
        return self.upload_dir.exists() and self.result_dir.exists()


class S3Storage(Storage):
    def __init__(self, settings: Settings):
        if not settings.s3_bucket:
            raise StorageError("S3_BUCKET must be configured when STORAGE_BACKEND=s3")
        try:
            import boto3
        except ImportError as exc:
            raise StorageError("boto3 is required for S3 storage") from exc
        self.bucket = settings.s3_bucket
        self.client = boto3.client("s3", region_name=settings.aws_region)

    def save_upload(self, document_id: str, filename: str, content: bytes) -> str:
        key = f"uploads/{document_id}/{Path(filename).name}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return f"s3://{self.bucket}/{key}"

    def save_result(self, document_id: str, result: dict[str, Any]) -> str:
        key = f"results/{document_id}.json"
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(result, default=str).encode("utf-8"),
            ContentType="application/json",
        )
        return f"s3://{self.bucket}/{key}"

    def get_result(self, document_id: str) -> dict[str, Any]:
        key = f"results/{document_id}.json"
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return json.loads(response["Body"].read().decode("utf-8"))

    def ready(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except Exception:
            return False


def build_storage(settings: Settings) -> Storage:
    if settings.storage_backend == "s3":
        return S3Storage(settings)
    return LocalStorage(settings)

