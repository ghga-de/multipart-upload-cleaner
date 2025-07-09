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

"""Config Parameter Modeling and Parsing."""

from typing import Annotated

from hexkit.config import config_from_yaml
from hexkit.log import LoggingConfig
from hexkit.providers.s3 import S3Config
from pydantic import Field

SERVICE_NAME: str = "multipart_upload_cleaner"


@config_from_yaml(prefix=SERVICE_NAME)
class Config(LoggingConfig, S3Config):
    """Config parameters and their defaults."""

    stale_after_days: Annotated[
        int,
        Field(
            default=...,
            ge=0,
            description=(
                "Number of days after which an open multipart upload is considered stale"
                " and safe to abort. 0 is allowed to immediately abort all currently"
                " ongoing multipart uploads for a given bucket."
            ),
        ),
    ]
    bucket_id: Annotated[
        str,
        Field(
            default=...,
            description="ID of the bucket that should be checked for stale multipart uploads.",
        ),
    ]
