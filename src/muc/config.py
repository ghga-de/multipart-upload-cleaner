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
"""Configuration for the multipart upload cleaner."""

from typing import Annotated

from hexkit.config import config_from_yaml
from hexkit.log import LoggingConfig
from hexkit.providers.s3 import S3Config
from pydantic import Field

SERVICE_NAME = "muc"


@config_from_yaml(SERVICE_NAME)
class Config(S3Config, LoggingConfig):
    """Custom configuration for multipart cleanup logic."""

    buckets: list[str] = Field(
        default=...,
        description="List of bucket IDs to check for stale multipart uploads.",
    )
    cleanup_interval: Annotated[
        int,
        Field(
            default=...,
            description="Number of days after which multipart uploads are considered stale and will be aborted."
            "0 is allowed to remove all multipart uploads regardless of their age.",
            ge=0,
        ),
    ]
