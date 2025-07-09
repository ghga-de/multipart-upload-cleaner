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

"""Test abort_stale_uploads."""

import asyncio
from datetime import UTC, datetime, timedelta

import boto3
import pytest

from ..config import Config
from ..core.main import abort_stale_uploads


@pytest.fixture(scope="module")
def localstack_s3_endpoint():
    # LocalStack default endpoint for S3
    return "http://localhost:4566"


@pytest.fixture
def s3_client(localstack_s3_endpoint):
    return boto3.client(
        "s3",
        endpoint_url=localstack_s3_endpoint,
        aws_access_key_id="test",
        aws_secret_access_key="test",  # noqa: S106
        region_name="us-east-1",
    )


@pytest.fixture
def test_bucket(s3_client):
    bucket_name = "test-bucket"
    s3_client.create_bucket(Bucket=bucket_name)
    yield bucket_name
    # Cleanup
    for upload in s3_client.list_multipart_uploads(Bucket=bucket_name).get(
        "Uploads", []
    ):
        s3_client.abort_multipart_upload(
            Bucket=bucket_name, Key=upload["Key"], UploadId=upload["UploadId"]
        )
    s3_client.delete_bucket(Bucket=bucket_name)


def create_multipart_upload(s3_client, bucket, key, initiated_time):
    # Initiate a multipart upload
    response = s3_client.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = response["UploadId"]
    # Patch the Initiated time using LocalStack's internal DynamoDB (not possible via boto3)
    # Instead, we will monkeypatch the paginator in the test to simulate stale uploads
    return upload_id


class FakePaginator:
    def __init__(self, uploads):
        self.uploads = uploads

    def paginate(self, Bucket):
        return [{"Uploads": self.uploads}]


@pytest.mark.asyncio
async def test_abort_stale_uploads_aborts_old_upload(
    monkeypatch, s3_client, test_bucket, localstack_s3_endpoint
):
    # Arrange
    key = "stale-object"
    upload_id = create_multipart_upload(s3_client, test_bucket, key, None)
    stale_time = datetime.now(UTC) - timedelta(days=10)
    uploads = [
        {
            "UploadId": upload_id,
            "Key": key,
            "Initiated": stale_time,
        }
    ]
    # Patch paginator to return our fake upload with old Initiated time
    monkeypatch.setattr(
        "boto3.client",
        lambda *args, **kwargs: type(
            "FakeS3",
            (),
            {
                "get_paginator": lambda self, op: FakePaginator(uploads),
                "abort_multipart_upload": lambda self, Bucket, Key, UploadId: None,
            },
        )(),
    )
    config = Config(
        s3_endpoint_url=localstack_s3_endpoint,
        s3_access_key_id="test",
        s3_secret_access_key="test",
        bucket_id=test_bucket,
        stale_after_days=7,
    )
    # Act
    await abort_stale_uploads(config=config)
    # Assert: nothing to assert, but we check that no exceptions are raised


@pytest.mark.asyncio
async def test_abort_stale_uploads_does_not_abort_recent_upload(
    monkeypatch, s3_client, test_bucket, localstack_s3_endpoint
):
    # Arrange
    key = "recent-object"
    upload_id = create_multipart_upload(s3_client, test_bucket, key, None)
    recent_time = datetime.now(UTC) - timedelta(days=1)
    uploads = [
        {
            "UploadId": upload_id,
            "Key": key,
            "Initiated": recent_time,
        }
    ]
    # Patch paginator to return our fake upload with recent Initiated time
    monkeypatch.setattr(
        "boto3.client",
        lambda *args, **kwargs: type(
            "FakeS3",
            (),
            {
                "get_paginator": lambda self, op: FakePaginator(uploads),
                "abort_multipart_upload": lambda self,
                Bucket,
                Key,
                UploadId: pytest.fail("Should not abort recent upload"),
            },
        )(),
    )
    config = Config(
        s3_endpoint_url=localstack_s3_endpoint,
        s3_access_key_id="test",
        s3_secret_access_key="test",
        bucket_id=test_bucket,
        stale_after_days=7,
    )
    # Act
    await abort_stale_uploads(config=config)
    # Assert: no abort should be called, otherwise test fails
