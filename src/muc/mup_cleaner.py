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
    """TODO"""

    def __init__(self, config: CleanerConfig):
        """Initialize the cleaner with the provided configuration."""
        self._config = config

    def run(self):
        """Run the multipart upload cleanup process."""
        logger.info("Starting multipart upload cleanup process.")
        self.abort_stale_multipart_uploads()
        logger.info("Multipart upload cleanup process completed.")

    def abort_stale_multipart_uploads(self):
        """Abort ongoing multipart uploads older than the configured interval for all buckets in the config."""
        client = boto3.client(
            "s3",
            aws_access_key_id=self._config.s3_access_key_id,
            aws_secret_access_key=self._config.s3_secret_access_key,
            endpoint_url=self._config.s3_endpoint_url,
        )
        threshold = datetime.now(UTC) - timedelta(days=self._config.cleanup_interval)

        num_uploads = 0
        number_aborted = 0

        for bucket in self._config.bucket_ids:
            paginator = client.get_paginator("list_multipart_uploads")
            for page in paginator.paginate(Bucket=bucket):
                uploads = page.get("Uploads", [])
                for upload in uploads:
                    num_uploads += 1

                    upload_id = upload["UploadId"]
                    key = upload["Key"]
                    initiated = upload["Initiated"]

                    # convert initiated to datetime
                    initiated = datetime.fromisoformat(initiated.replace("Z", "+00:00"))
                    if initiated < threshold:
                        try:
                            client.abort_multipart_upload(
                                Bucket=bucket, Key=key, UploadId=upload_id
                            )
                        except ClientError as error:
                            logger.error(
                                f"Failed to abort upload {upload_id} for object {key} in bucket {bucket}, initiated on {initiated}:\n{error}"
                            )
                        logger.info(
                            f"Aborted upload {upload_id} for object {key} in bucket {bucket}, initiated on {initiated}."
                        )
                        number_aborted += 1
        logger.info(
            f"Aborted {number_aborted} stale multipart uploads out of {num_uploads} total uploads across {'buckets' if len(self._config.bucket_ids) > 1 else 'bucket'}."
        )
