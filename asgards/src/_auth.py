"""Shared authentication helper for all Asgards clients."""
import os

from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication


def _build_connection(pat: str | None, org_url: str | None) -> Connection:
    """Build an authenticated Azure DevOps connection.

    Args:
        pat: Personal Access Token. Falls back to AZURE_DEVOPS_PAT env var.
        org_url: Organization URL. Falls back to AZURE_DEVOPS_ORG_URL env var.

    Returns:
        An authenticated Connection instance.

    Raises:
        ValueError: If pat or org_url is missing from both sources.
    """
    pat = pat or os.environ.get("AZURE_DEVOPS_PAT")
    org_url = org_url or os.environ.get("AZURE_DEVOPS_ORG_URL")
    if not pat:
        raise ValueError("PAT required: pass 'pat' argument or set AZURE_DEVOPS_PAT env var")
    if not org_url:
        raise ValueError(
            "Org URL required: pass 'org_url' argument or set AZURE_DEVOPS_ORG_URL env var"
        )
    credentials = BasicAuthentication("", pat)
    return Connection(base_url=org_url, creds=credentials)
