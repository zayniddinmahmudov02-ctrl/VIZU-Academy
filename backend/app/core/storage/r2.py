"""Cloudflare R2 storage client for video assets.

R2 is S3-compatible, so this is a thin boto3 wrapper scoped to exactly
what the video-streaming flow needs: upload the raw bytes, delete an
object, check whether one exists, and mint a short-lived presigned GET
URL for streaming. It intentionally does not implement `BaseStorage`
(app/core/storage/base.py) — that interface models a public, permanent
`url()` for local-disk assets, which is the opposite of what private,
expiring video streaming needs. Kept alongside it in the same package
since it is still a storage provider, just not a drop-in for that ABC.
"""

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.logging.logger import logger


class R2StorageClient:
    """Reusable singleton client for Cloudflare R2 (S3-compatible).

    Access via `get_r2_client()` rather than instantiating directly, so
    the underlying boto3 client is built once per process.
    """

    def __init__(self) -> None:
        self.bucket = settings.R2_BUCKET_NAME

        self._client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name=settings.R2_REGION,
            config=BotoConfig(signature_version="s3v4"),
        )

    def upload_file(
        self,
        file_obj,
        key: str,
        content_type: str | None = None,
    ) -> str:
        """Uploads a file-like object to R2 under `key`.

        `file_obj` must be positioned at the start and support `.read()`
        (e.g. `UploadFile.file`). Returns the storage key on success.
        Raises `RuntimeError` on failure — callers should not need to
        know about botocore's exception types.
        """

        extra_args = {"ContentType": content_type} if content_type else {}

        try:
            self._client.upload_fileobj(
                file_obj,
                self.bucket,
                key,
                ExtraArgs=extra_args,
            )
        except ClientError as exc:
            logger.error("R2 upload failed for key=%s: %s", key, exc)
            raise RuntimeError(f"Failed to upload object '{key}' to R2") from exc

        return key

    def delete_file(self, key: str) -> None:
        """Deletes an object from R2. Silently no-ops if it doesn't exist
        (delete is idempotent by design — callers shouldn't have to check
        existence first)."""

        try:
            self._client.delete_object(
                Bucket=self.bucket,
                Key=key,
            )
        except ClientError as exc:
            logger.error("R2 delete failed for key=%s: %s", key, exc)
            raise RuntimeError(f"Failed to delete object '{key}' from R2") from exc

    def generate_signed_url(
        self,
        key: str,
        expires_in: int | None = None,
    ) -> str:
        """Returns a presigned GET URL for `key`, valid for `expires_in`
        seconds (defaults to settings.R2_SIGNED_URL_EXPIRE_SECONDS — 5
        minutes per the streaming-security spec). Never returns a
        permanent link."""

        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": key,
                },
                ExpiresIn=expires_in or settings.R2_SIGNED_URL_EXPIRE_SECONDS,
            )
        except ClientError as exc:
            logger.error("R2 signed URL generation failed for key=%s: %s", key, exc)
            raise RuntimeError(f"Failed to generate signed URL for '{key}'") from exc

    def object_exists(self, key: str) -> bool:
        """Checks whether `key` exists in the bucket via a HEAD request."""

        try:
            self._client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey", "NotFound"):
                return False
            logger.error("R2 object_exists check failed for key=%s: %s", key, exc)
            raise RuntimeError(f"Failed to check existence of '{key}' in R2") from exc


_r2_client: R2StorageClient | None = None


def get_r2_client() -> R2StorageClient:
    """Returns the process-wide R2StorageClient singleton, creating it on
    first use. Use as a FastAPI dependency or call directly from
    services."""

    global _r2_client

    if _r2_client is None:
        _r2_client = R2StorageClient()

    return _r2_client
