import os
import uuid
from dataclasses import dataclass
from typing import Protocol

from supabase import create_client


class StorageAdapter(Protocol):
    def upload(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        raise NotImplementedError

    def get_signed_url(self, storage_key: str, expires_in: int) -> str:
        raise NotImplementedError


@dataclass
class SupabaseStorageAdapter:
    url: str
    anon_key: str
    bucket: str

    def _client(self):
        return create_client(self.url, self.anon_key)

    def upload(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        storage_key = f"uploads/{uuid.uuid4()}/{filename}"
        client = self._client()
        client.storage.from_(self.bucket).upload(
            storage_key,
            file_bytes,
            {
                "content-type": content_type,
                "x-upsert": "true",
            },
        )
        return storage_key

    def get_signed_url(self, storage_key: str, expires_in: int) -> str:
        client = self._client()
        result = client.storage.from_(self.bucket).create_signed_url(storage_key, expires_in)
        return result.get("signedURL") or ""


@dataclass
class LocalStorageAdapter:
    base_path: str

    def upload(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        os.makedirs(self.base_path, exist_ok=True)
        storage_key = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(self.base_path, storage_key)
        with open(file_path, "wb") as file_handle:
            file_handle.write(file_bytes)
        return storage_key

    def get_signed_url(self, storage_key: str, expires_in: int) -> str:
        file_path = os.path.join(self.base_path, storage_key)
        return f"file://{os.path.abspath(file_path)}"


def get_storage_adapter() -> StorageAdapter:
    backend = os.getenv("STORAGE_BACKEND", "supabase").lower()
    if backend == "local":
        base_path = os.getenv("LOCAL_STORAGE_PATH", "./uploads")
        return LocalStorageAdapter(base_path=base_path)

    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    bucket = os.getenv("SUPABASE_BUCKET")
    if not url or not anon_key or not bucket:
        raise ValueError("Supabase storage requires SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_BUCKET")
    return SupabaseStorageAdapter(url=url, anon_key=anon_key, bucket=bucket)
