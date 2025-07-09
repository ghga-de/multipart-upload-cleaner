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
"""Core functionality."""

import logging
from datetime import UTC, datetime, timedelta

import boto3

from multipart_upload_cleaner.config import Config


async def abort_stale_uploads(config: Config = Config()):  # type: ignore
    """Abort ongoing multipart uploads past a configured threshold."""
    # Configure logging
    logger = logging.getLogger(__name__)

    # Calculate threshold datetime
    threshold_days = config.stale_after_days
    threshold = datetime.now(UTC) - timedelta(days=threshold_days)

    # Initialize S3 client
    s3 = boto3.client(
        "s3",
        endpoint_url=config.s3_endpoint_url,
        aws_access_key_id=config.s3_access_key_id,
        aws_secret_access_key=config.s3_secret_access_key,
    )

    # List all multipart uploads
    paginator = s3.get_paginator("list_multipart_uploads")
    aborted_uploads = []
    num_uploads = 0
    for page in paginator.paginate(Bucket=config.bucket_id):
        uploads = page.get("Uploads", [])
        for upload in uploads:
            num_uploads += 1
            upload_id = upload["UploadId"]
            key = upload["Key"]
            initiated = upload["Initiated"]
            if initiated < threshold:
                logger.info(
                    f"Aborting stale upload: {key} (UploadId: {upload_id}, Initiated: {initiated})"
                )
                s3.abort_multipart_upload(
                    Bucket=config.bucket_id, Key=key, UploadId=upload_id
                )
                aborted_uploads.append(
                    {"Key": key, "UploadId": upload_id, "Initiated": initiated}
                )

    logger.info(
        f"Aborted {len(aborted_uploads)} of {num_uploads} stale multipart uploads."
    )
