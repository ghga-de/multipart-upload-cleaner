# Copyright 2021 - 2025 Universität Tübingen, DKFZ, EMBL, and Universität zu Köln
# for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Core multipart upload cleaner logic."""

from datetime import UTC, datetime, timedelta
from logging import getLogger

import boto3
from botocore.exceptions import ClientError
from hexkit.log import LoggingConfig
from hexkit.providers.s3 import S3Config
from pydantic import Field

logger = getLogger(__name__)


class CleanerConfig(S3Config, LoggingConfig):
    """Custom configuration for multipart cleanup logic."""

    bucket_ids: list[str] = Field(
        default=...,
        description="List of bucket IDs to check for stale multipart uploads.",
    )
    cleanup_interval: int = Field(
        default=...,
        description="Number of days after which multipart uploads are considered stale and will be aborted.",
    )


class MultipartUploadCleaner:
    """Handler class for cleanup of stale multipart uploads in S3 buckets."""

    def __init__(self, config: CleanerConfig):
        """Initialize the cleaner with the provided configuration."""
        self._config = config
        self._client = boto3.client(
            "s3",
            aws_access_key_id=config.s3_access_key_id,
            aws_secret_access_key=config.s3_secret_access_key,
            endpoint_url=config.s3_endpoint_url,
        )
        self._threshold = datetime.now(UTC) - timedelta(days=config.cleanup_interval)

    def run(self):
        """Run the multipart upload cleanup process."""
        logger.info("Starting multipart upload cleanup process.")
        self.abort_stale_multipart_uploads()
        logger.info("Multipart upload cleanup process completed.")

    def abort_stale_multipart_uploads(self):
        """Abort ongoing multipart uploads older than the configured interval for all buckets in the config."""
        for bucket in self._config.bucket_ids:
            paginator = self._client.get_paginator("list_multipart_uploads")
            for page in paginator.paginate(Bucket=bucket):
                self._handle_pages(bucket=bucket, page=page)

    def _handle_pages(self, *, bucket: str, page):
        """Handle each page in the list of multipart uploads."""
        uploads = page.get("Uploads", [])
        for upload in uploads:
            self._handle_upload(
                bucket=bucket,
                upload_id=upload["UploadId"],
                key=upload["Key"],
                initiated=upload["Initiated"],
            )

    def _handle_upload(self, *, bucket: str, upload_id: str, key: str, initiated: str):
        """Handle a single multipart upload."""
        started = datetime.fromisoformat(initiated.replace("Z", "+00:00"))
        if started < self._threshold:
            try:
                self._client.abort_multipart_upload(
                    Bucket=bucket, Key=key, UploadId=upload_id
                )
            except ClientError as error:
                logger.error(
                    f"Failed to abort upload {upload_id} for object {key} in bucket {bucket}, initiated on {started}:\n{error}"
                )
            logger.info(
                f"Aborted upload {upload_id} for object {key} in bucket {bucket}, initiated on {started}."
            )
