"""S3-compatible blob resource.

Thin wrapper over boto3 against the ``s3_endpoint_url`` (MinIO at PoC,
real S3 in Stage 01). Surfaces only the verbs we actually use so the
fake in tests is small.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import boto3
from botocore.client import Config
from dagster import ConfigurableResource


class MinioResource(ConfigurableResource):
    endpoint_url: str
    access_key: str
    secret_key: str
    region: str = "us-east-1"  # MinIO ignores it; boto3 demands one.

    def _client(self) -> Any:
        return boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            config=Config(s3={"addressing_style": "path"}),
        )

    def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self._client().put_object(
            Bucket=bucket, Key=key, Body=data, ContentType=content_type
        )

    def get_bytes(self, bucket: str, key: str) -> bytes:
        return self._client().get_object(Bucket=bucket, Key=key)["Body"].read()

    @contextmanager
    def open_for_writing(self, bucket: str, key: str) -> Iterator[bytearray]:
        """Accumulate bytes locally and put on context exit. Tiny convenience."""
        buf = bytearray()
        try:
            yield buf
        finally:
            self.put_bytes(bucket, key, bytes(buf), "application/octet-stream")
