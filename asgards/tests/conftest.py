"""Pytest configuration for the Asgards test suite."""

import os
from unittest.mock import MagicMock

from azure.devops.exceptions import AzureDevOpsServiceError

os.environ.setdefault("HOME", "/tmp")


def make_service_error(message: str, status_code: int | None = None) -> AzureDevOpsServiceError:
    """Build an AzureDevOpsServiceError instance compatible with the SDK."""
    wrapped = MagicMock()
    wrapped.inner_exception = None
    wrapped.message = message
    error = AzureDevOpsServiceError(wrapped)
    if status_code is not None:
        error.status_code = status_code
    return error
