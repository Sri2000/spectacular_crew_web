"""
S3 upload service.

Uploads raw file bytes to the configured S3 bucket.
All public methods return a result dict and never raise — callers
can decide whether to treat a failure as fatal.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import settings

logger = logging.getLogger(__name__)

_CONTENT_TYPES = {
    "csv":  "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xls":  "application/vnd.ms-excel",
}


class S3Service:
    """Thin wrapper around boto3 S3 client for file uploads."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        self._bucket = settings.AWS_S3_BUCKET

    def upload_file_bytes(
        self,
        file_bytes: bytes,
        filename: str,
        data_type: str,
    ) -> Dict[str, Any]:
        """
        Upload raw file bytes to S3.

        S3 key format: uploads/{data_type}/{timestamp}_{filename}
        e.g.           uploads/sales/20240315T143022Z_sales_q1.csv

        Returns a dict with keys:
          success  (bool)
          s3_key   (str | None)
          s3_url   (str | None)
          error    (str | None)
        Never raises.
        """
        ext = (filename or "").lower().rsplit(".", 1)[-1]
        content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        s3_key = f"uploads/{data_type}/{timestamp}_{filename}"

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=content_type,
            )
            s3_url = (
                f"https://{self._bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            )
            logger.info("Uploaded to S3: %s", s3_key)
            return {"success": True, "s3_key": s3_key, "s3_url": s3_url, "error": None}

        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 upload failed for '%s': %s", s3_key, exc)
            return {"success": False, "s3_key": None, "s3_url": None, "error": str(exc)}
