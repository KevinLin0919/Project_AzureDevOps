"""Azure DevOps Project management operations."""

from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.core.models import TeamProject

from asgards.src._auth import _build_connection

PROCESS_TEMPLATE_IDS = {
    "agile": "adcc42ab-9882-485e-a3ed-7678f01f66bc",
    "scrum": "6b724908-ef14-45cf-84f8-768b5384da45",
    "cmmi": "27450541-8e31-4150-9947-dc59f998fc01",
}


class ProjectClient:
    """CRUD operations and existence checks for Azure DevOps projects."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client.

        Credentials via constructor args or env vars AZURE_DEVOPS_PAT / AZURE_DEVOPS_ORG_URL.
        """
        connection = _build_connection(pat, org_url)
        self._client = connection.clients.get_core_client()

    def create(self, name: str, description: str = "", process_template: str = "Agile"):
        """Create a new Azure DevOps project. Returns an OperationReference (async)."""
        template_id = PROCESS_TEMPLATE_IDS.get(
            process_template.strip().lower(),
            process_template,
        )
        project_params = TeamProject(
            name=name,
            description=description,
            capabilities={
                "versioncontrol": {"sourceControlType": "Git"},
                "processTemplate": {"templateTypeId": template_id},
            },
        )
        try:
            return self._client.queue_create_project(project_params)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to create project '{name}': {e}") from e

    def get(self, project_id_or_name: str):
        """Get project info by name or ID. Raises RuntimeError if not found."""
        try:
            return self._client.get_project(project_id_or_name)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get project '{project_id_or_name}': {e}") from e

    def list(self):
        """List all projects in the organization."""
        try:
            return self._client.get_projects()
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to list projects: {e}") from e

    def delete(self, project_id: str):
        """Delete a project by ID. Returns an OperationReference (async)."""
        try:
            return self._client.queue_delete_project(project_id)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to delete project '{project_id}': {e}") from e

    def exists(self, name: str) -> bool:
        """Return True if the project exists, False otherwise. Never raises."""
        try:
            self._client.get_project(name)
            return True
        except AzureDevOpsServiceError as e:
            if getattr(e, "status_code", None) == 404 or "404" in str(e):
                return False
            raise RuntimeError(f"Failed to check project '{name}': {e}") from e
