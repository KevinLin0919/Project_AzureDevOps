"""Azure DevOps Pipeline configuration and trigger operations."""

from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.build.models import Build, BuildDefinition, BuildRepository

from asgards.src._auth import _build_connection

_STATUS_MAP = {
    "notstarted": "queued",
    "postponed": "queued",
    "inprogress": "running",
}
_RESULT_MAP = {
    "succeeded": "succeeded",
    "partiallysucceeded": "succeeded",
    "failed": "failed",
    "canceled": "canceled",
}


class PipelineClient:
    """Create build definitions from YAML, trigger runs, and check run status."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client with explicit credentials or env-var fallbacks."""
        connection = _build_connection(pat, org_url)
        self._client = connection.clients.get_build_client()

    def create_from_yaml(
        self,
        project: str,
        name: str,
        repo_id: str,
        yaml_path: str,
        default_branch: str = "main",
    ):
        """Create a build pipeline definition pointing to a YAML file in a repo."""
        definition = BuildDefinition(
            name=name,
            repository=BuildRepository(
                id=repo_id,
                type="TfsGit",
                default_branch=f"refs/heads/{default_branch}",
            ),
            process={"yamlFilename": yaml_path, "type": 2},
        )
        try:
            return self._client.create_definition(definition, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to create pipeline '{name}': {e}") from e

    def list(self, project: str):
        """List all pipeline definitions in the given project."""
        try:
            return self._client.get_definitions(project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to list pipelines in '{project}': {e}") from e

    def trigger(self, project: str, definition_id: int):
        """Queue a new build run for the given pipeline definition."""
        build = Build(definition={"id": definition_id})
        try:
            return self._client.queue_build(build, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to trigger pipeline {definition_id}: {e}") from e

    def get_run_status(self, project: str, build_id: int) -> str:
        """Return the normalized status of a build run.

        Returns one of: "queued", "running", "succeeded", "failed", "canceled".
        """
        try:
            build = self._client.get_build(project, build_id)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get build {build_id}: {e}") from e

        status = str(build.status).lower() if build.status else ""
        result = str(build.result).lower() if build.result else ""

        if status in _STATUS_MAP:
            return _STATUS_MAP[status]
        if status == "completed":
            return _RESULT_MAP.get(result, "failed")
        return "queued"
