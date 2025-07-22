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

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from muc.mup_cleaner import CleanerConfig, MultipartUploadCleaner


@pytest.fixture
def config():
    """Simple test configuration for the cleaner."""
    return CleanerConfig(
        s3_access_key_id="testy",
        s3_secret_access_key="test",
        s3_endpoint_url="http://localstack:4566",
        bucket_ids=["bucket1", "bucket2"],
        cleanup_interval=7,
        service_name="test-service",
        service_instance_id="test001",
    )


@pytest.fixture
def uploads(now):
    """Provide a list of mock multipart upload metadata."""
    return [
        {
            "UploadId": "old-upload",
            "Key": "file1.txt",
            "Initiated": (now - timedelta(days=10)).isoformat().replace("+00:00", "Z"),
        },
        {
            "UploadId": "recent-upload",
            "Key": "file2.txt",
            "Initiated": (now - timedelta(days=2)).isoformat().replace("+00:00", "Z"),
        },
    ]


@pytest.fixture
def now():
    """Fixed point in time for tests."""
    return datetime(2025, 8, 12, 16, 4, 0, tzinfo=UTC)


def test_abort_stale_multipart_uploads_aborts_old_uploads(
    mock_datetime, mock_boto_client, config, uploads, now
):
    """TODO"""
    mock_datetime.now.return_value = now
    mock_datetime.fromisoformat.side_effect = lambda s: datetime.fromisoformat(
        s.replace("Z", "+00:00")
    )
    mock_datetime.UTC = UTC

    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    paginator = MagicMock()
    paginator.paginate.side_effect = lambda Bucket: [{"Uploads": uploads}]
    mock_client.get_paginator.return_value = paginator

    # Run
    summary = abort_stale_multipart_uploads(config)

    # Only the old upload should be aborted for each bucket
    for bucket in config.bucket_ids:
        assert len(summary[bucket]) == 1
        aborted = summary[bucket][0]
        assert aborted["key"] == "file1.txt"
        assert aborted["upload_id"] == "old-upload"
        assert isinstance(aborted["initiated"], datetime)
        # Check abort_multipart_upload called with correct args
        mock_client.abort_multipart_upload.assert_any_call(
            Bucket=bucket, Key="file1.txt", UploadId="old-upload"
        )
    # Should not abort recent upload
    assert mock_client.abort_multipart_upload.call_count == len(config.bucket_ids)


def test_abort_stale_multipart_uploads_no_uploads(
    mock_datetime, mock_boto_client, config, now
):
    """TODO"""
    mock_datetime.now.return_value = now
    mock_datetime.UTC = UTC

    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    paginator = MagicMock()
    paginator.paginate.side_effect = lambda Bucket: [{"Uploads": []}]
    mock_client.get_paginator.return_value = paginator

    summary = abort_stale_multipart_uploads(config)
    for bucket in config.bucket_ids:
        assert summary[bucket] == []
    mock_client.abort_multipart_upload.assert_not_called()


def test_abort_stale_multipart_uploads_initiated_as_datetime(
    mock_datetime, mock_boto_client, config, now
):
    """TODO"""
    mock_datetime.now.return_value = now
    mock_datetime.UTC = UTC

    mock_client = MagicMock()
    mock_boto_client.return_value = mock_client

    old_dt = now - timedelta(days=10)
    uploads = [
        {
            "UploadId": "old-upload",
            "Key": "file1.txt",
            "Initiated": old_dt,
        }
    ]
    paginator = MagicMock()
    paginator.paginate.side_effect = lambda Bucket: [{"Uploads": uploads}]
    mock_client.get_paginator.return_value = paginator

    summary = abort_stale_multipart_uploads(config)
    for bucket in config.bucket_ids:
        assert len(summary[bucket]) == 1
        assert summary[bucket][0]["key"] == "file1.txt"
    mock_client.abort_multipart_upload.assert_any_call(
        Bucket=config.bucket_ids[0], Key="file1.txt", UploadId="old-upload"
    )
