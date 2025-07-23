[![tests](https://github.com/ghga-de/multipart-upload-cleaner/actions/workflows/tests.yaml/badge.svg)](https://github.com/ghga-de/multipart-upload-cleaner/actions/workflows/tests.yaml)
[![Coverage Status](https://coveralls.io/repos/github/ghga-de/multipart-upload-cleaner/badge.svg?branch=main)](https://coveralls.io/github/ghga-de/multipart-upload-cleaner?branch=main)

# Multipart Upload Cleaner

Multipart Upload Cleaner - Small script to abort ongoing multipart uploads

## Description

<!-- Please provide a short overview of the features of this service. -->

Here you should provide a short summary of the purpose of this microservice.


## Installation

We recommend using the provided Docker container.

A pre-built version is available at [docker hub](https://hub.docker.com/repository/docker/ghga/multipart-upload-cleaner):
```bash
docker pull ghga/multipart-upload-cleaner:0.1.0
```

Or you can build the container yourself from the [`./Dockerfile`](./Dockerfile):
```bash
# Execute in the repo's root dir:
docker build -t ghga/multipart-upload-cleaner:0.1.0 .
```

For production-ready deployment, we recommend using Kubernetes, however,
for simple use cases, you could execute the service using docker
on a single server:
```bash
# The entrypoint is preconfigured:
docker run -p 8080:8080 ghga/multipart-upload-cleaner:0.1.0 --help
```

If you prefer not to use containers, you may install the service from source:
```bash
# Execute in the repo's root dir:
pip install .

# To run the service:
muc --help
```

## Configuration

### Parameters

The service requires the following configuration parameters:
- <a id="properties/log_level"></a>**`log_level`** *(string)*: The minimum log level to capture. Must be one of: "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", or "TRACE". Default: `"INFO"`.

- <a id="properties/service_name"></a>**`service_name`** *(string, required)*: The name of the (micro-)service. This will be included in log messages.


  Examples:

  ```json
  "my-cool-special-service"
  ```


- <a id="properties/service_instance_id"></a>**`service_instance_id`** *(string, required)*: A string that uniquely identifies this instance across all instances of this service. This is included in log messages.


  Examples:

  ```json
  "germany-bw-instance-001"
  ```


- <a id="properties/log_format"></a>**`log_format`**: If set, will replace JSON formatting with the specified string format. If not set, has no effect. In addition to the standard attributes, the following can also be specified: timestamp, service, instance, level, correlation_id, and details. Default: `null`.

  - **Any of**

    - <a id="properties/log_format/anyOf/0"></a>*string*

    - <a id="properties/log_format/anyOf/1"></a>*null*


  Examples:

  ```json
  "%(timestamp)s - %(service)s - %(level)s - %(message)s"
  ```


  ```json
  "%(asctime)s - Severity: %(levelno)s - %(msg)s"
  ```


- <a id="properties/log_traceback"></a>**`log_traceback`** *(boolean)*: Whether to include exception tracebacks in log messages. Default: `true`.

- <a id="properties/s3_endpoint_url"></a>**`s3_endpoint_url`** *(string, required)*: URL to the S3 API.


  Examples:

  ```json
  "http://localhost:4566"
  ```


- <a id="properties/s3_access_key_id"></a>**`s3_access_key_id`** *(string, required)*: Part of credentials for login into the S3 service. See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html.


  Examples:

  ```json
  "my-access-key-id"
  ```


- <a id="properties/s3_secret_access_key"></a>**`s3_secret_access_key`** *(string, format: password, required and write-only)*: Part of credentials for login into the S3 service. See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html.


  Examples:

  ```json
  "my-secret-access-key"
  ```


- <a id="properties/s3_session_token"></a>**`s3_session_token`**: Part of credentials for login into the S3 service. See: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html. Default: `null`.

  - **Any of**

    - <a id="properties/s3_session_token/anyOf/0"></a>*string, format: password*

    - <a id="properties/s3_session_token/anyOf/1"></a>*null*


  Examples:

  ```json
  "my-session-token"
  ```


- <a id="properties/aws_config_ini"></a>**`aws_config_ini`**: Path to a config file for specifying more advanced S3 parameters. This should follow the format described here: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-a-configuration-file. Default: `null`.

  - **Any of**

    - <a id="properties/aws_config_ini/anyOf/0"></a>*string, format: path*

    - <a id="properties/aws_config_ini/anyOf/1"></a>*null*


  Examples:

  ```json
  "~/.aws/config"
  ```


- <a id="properties/buckets"></a>**`buckets`** *(array, required)*: List of bucket IDs to check for stale multipart uploads.

  - <a id="properties/buckets/items"></a>**Items** *(string)*

- <a id="properties/cleanup_interval"></a>**`cleanup_interval`** *(integer, required)*: Number of days after which multipart uploads are considered stale and will be aborted.0 is allowed to remove all multipart uploads regardless of their age. Minimum: `0`.


### Usage:

A template YAML for configuring the service can be found at
[`./example_config.yaml`](./example_config.yaml).
Please adapt it, rename it to `.muc.yaml`, and place it in one of the following locations:
- in the current working directory where you execute the service (on Linux: `./.muc.yaml`)
- in your home directory (on Linux: `~/.muc.yaml`)

The config yaml will be automatically parsed by the service.

**Important: If you are using containers, the locations refer to paths within the container.**

All parameters mentioned in the [`./example_config.yaml`](./example_config.yaml)
could also be set using environment variables or file secrets.

For naming the environment variables, just prefix the parameter name with `muc_`,
e.g. for the `host` set an environment variable named `muc_host`
(you may use both upper or lower cases, however, it is standard to define all env
variables in upper cases).

To use file secrets, please refer to the
[corresponding section](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support)
of the pydantic documentation.



## Architecture and Design:
<!-- Please provide an overview of the architecture and design of the code base.
Mention anything that deviates from the standard Triple Hexagonal Architecture and
the corresponding structure. -->

This is a Python-based service following the Triple Hexagonal Architecture pattern.
It uses protocol/provider pairs and dependency injection mechanisms provided by the
[hexkit](https://github.com/ghga-de/hexkit) library.


## Development

For setting up the development environment, we rely on the
[devcontainer feature](https://code.visualstudio.com/docs/remote/containers) of VS Code
in combination with Docker Compose.

To use it, you have to have Docker Compose as well as VS Code with its "Remote - Containers"
extension (`ms-vscode-remote.remote-containers`) installed.
Then open this repository in VS Code and run the command
`Remote-Containers: Reopen in Container` from the VS Code "Command Palette".

This will give you a full-fledged, pre-configured development environment including:
- infrastructural dependencies of the service (databases, etc.)
- all relevant VS Code extensions pre-installed
- pre-configured linting and auto-formatting
- a pre-configured debugger
- automatic license-header insertion

Moreover, inside the devcontainer, a command `dev_install` is available for convenience.
It installs the service with all development dependencies, and it installs pre-commit.

The installation is performed automatically when you build the devcontainer. However,
if you update dependencies in the [`./pyproject.toml`](./pyproject.toml) or the
[`lock/requirements-dev.txt`](./lock/requirements-dev.txt), please run it again.

## License

This repository is free to use and modify according to the
[Apache 2.0 License](./LICENSE).

## README Generation

This README file is auto-generated, please see [.readme_generation/README.md](./.readme_generation/README.md)
for details.
