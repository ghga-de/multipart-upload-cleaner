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
"""Test multipart upload cleaner logic."""

from contextlib import contextmanager
from datetime import UTC, datetime

import boto3
from testcontainers.localstack import LocalStackContainer

from muc.mup_cleaner import CleanerConfig, MultipartUploadCleaner

BUCKET_IDS = ["bucket1", "bucket2"]
FILE_IDS = ["file1.txt", "file2.txt", "file3.txt"]
CLEANUP_INTERVAL = 7  # days
NOW = datetime(2025, 8, 12, 16, 4, tzinfo=UTC)
TEST_CONFIG = CleanerConfig(
    s3_access_key_id="test",
    s3_secret_access_key="test",
    s3_endpoint_url="http://localstack:4566",
    bucket_ids=BUCKET_IDS,
    cleanup_interval=7,
    service_name="test-service",
    service_instance_id="test001",
)  # type: ignore

# List of mock multipart upload metadata
# Only the second upload is stale and should be aborted
MOCK_METADATA_REPLACEMENTS = {
    "file1.txt": {"Initiated": datetime(2025, 8, 12, tzinfo=UTC).isoformat()},
    "file2.txt": {"Initiated": datetime(2025, 8, 5, tzinfo=UTC).isoformat()},
    "file3.txt": {
        "Initiated": datetime(2025, 8, 5, 23, 59, 59, tzinfo=UTC).isoformat()
    },
}


@contextmanager
def patch_handle_upload():
    """Patch the `_handle_upload` method to inject fake upload initiation dates."""
    original = MultipartUploadCleaner._handle_upload

    def patch(self, *, bucket: str, upload_id: str, key: str, initiated: str):
        """Patch to inject fake upload initiation date."""
        original(
            self,
            bucket=bucket,
            upload_id=upload_id,
            key=key,
            initiated=MOCK_METADATA_REPLACEMENTS[key]["Initiated"],
        )

    MultipartUploadCleaner._handle_upload = patch
    yield
    MultipartUploadCleaner._handle_upload = original


def test_multipart_upload_cleaner_with_localstack():
    """Populate buckets with different test uploads and run the cleaner."""
    with LocalStackContainer(image="localstack/localstack:latest") as localstack:
        endpoint_url = localstack.get_url()
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=TEST_CONFIG.s3_access_key_id,
            aws_secret_access_key=TEST_CONFIG.s3_secret_access_key,
            endpoint_url=endpoint_url,
        )
        for bucket in TEST_CONFIG.bucket_ids:
            s3_client.create_bucket(Bucket=bucket)

        # Create mock multipart uploads
        s3_client.create_multipart_upload(
            Bucket="bucket1",
            Key="file1.txt",
        )
        s3_client.create_multipart_upload(
            Bucket="bucket1",
            Key="file2.txt",
        )
        s3_client.create_multipart_upload(
            Bucket="bucket2",
            Key="file3.txt",
        )

        config = TEST_CONFIG.model_copy(update={"s3_endpoint_url": endpoint_url})
        with patch_handle_upload():
            cleaner = MultipartUploadCleaner(config)
            cleaner.abort_stale_multipart_uploads()

        # Verify that only the stale upload was aborted
        bucket1_uploads = s3_client.list_multipart_uploads(Bucket="bucket1")["Uploads"]
        assert len(bucket1_uploads) == 1
        assert bucket1_uploads[0]["Key"] == "file1.txt"

        bucket2_uploads = s3_client.list_multipart_uploads(Bucket="bucket2")["Uploads"]
        assert len(bucket2_uploads) == 1
        assert bucket2_uploads[0]["Key"] == "file3.txt"
