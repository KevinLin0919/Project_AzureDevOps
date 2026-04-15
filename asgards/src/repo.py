"""Azure DevOps Repository operations."""

from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.git.models import (
    GitCommit,
    GitPush,
    GitRefUpdate,
    GitRepository,
    GitVersionDescriptor,
    ItemContent,
)

from asgards.src._auth import _build_connection

FILE_SIZE_LIMIT_BYTES = 5 * 1024 * 1024  # 5 MB


class RepoClient:
    """CRUD and file-content operations for Azure DevOps Git repositories."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client with explicit credentials or env-var fallbacks."""
        self._connection = _build_connection(pat, org_url)
        self._client = self._connection.clients.get_git_client()

    def create(self, project: str, name: str):
        """Create a new Git repository in the given project."""
        repo = GitRepository(name=name)
        try:
            return self._client.create_repository(repo, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to create repo '{name}': {e}") from e

    def get(self, project: str, repo_id_or_name: str):
        """Get a repository by ID or name."""
        try:
            return self._client.get_repository(repo_id_or_name, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get repo '{repo_id_or_name}': {e}") from e

    def list(self, project: str):
        """List all repositories in the given project."""
        try:
            return self._client.get_repositories(project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to list repos in '{project}': {e}") from e

    def delete(self, project: str, repo_id: str) -> None:
        """Delete a repository by ID."""
        try:
            self._client.delete_repository(repo_id, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to delete repo '{repo_id}': {e}") from e

    def get_file_content(
        self,
        project: str,
        repo_id: str,
        file_path: str,
        branch: str = "main",
    ) -> str:
        """Retrieve the raw content of a file from a repository."""
        version = GitVersionDescriptor(version=branch, version_type="branch")
        try:
            stream = self._client.get_item_content(
                repo_id,
                file_path,
                project,
                version_descriptor=version,
            )
            return b"".join(stream).decode("utf-8")
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get file '{file_path}': {e}") from e

    def get_file_content_from_source(
        self,
        src_org_url: str,
        src_pat: str,
        src_project: str,
        src_repo: str,
        file_path: str,
        branch: str = "main",
    ) -> str:
        """Retrieve file content from a different organization/project/repo."""
        src_connection = _build_connection(src_pat, src_org_url)
        src_client = src_connection.clients.get_git_client()
        version = GitVersionDescriptor(version=branch, version_type="branch")
        try:
            stream = src_client.get_item_content(
                src_repo,
                file_path,
                src_project,
                version_descriptor=version,
            )
            return b"".join(stream).decode("utf-8")
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get file '{file_path}' from source: {e}") from e

    def push_file(
        self,
        project: str,
        repo_id: str,
        file_path: str,
        content: str | bytes,
        branch: str = "main",
        commit_message: str = "chore: update file via asgards",
    ):
        """Push (create or update) a file to a repository as a new commit.

        Raises:
            ValueError: If content exceeds the 5 MB file size limit.
            RuntimeError: On Azure DevOps API errors.
        """
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        if len(content_bytes) > FILE_SIZE_LIMIT_BYTES:
            raise ValueError(
                "Content size "
                f"{len(content_bytes)} bytes exceeds the 5 MB limit "
                f"({FILE_SIZE_LIMIT_BYTES} bytes)"
            )

        # Determine whether this is an add (1) or edit (2)
        change_type = 1
        try:
            self._client.get_item(repo_id, file_path, project)
            change_type = 2
        except AzureDevOpsServiceError:
            change_type = 1

        # Get current branch SHA for the ref update
        refs = self._client.get_refs(repo_id, project, filter=f"heads/{branch}")
        old_sha = refs[0].object_id if refs else "0000000000000000000000000000000000000000"

        push = GitPush(
            commits=[
                GitCommit(
                    comment=commit_message,
                    changes=[
                        {
                            "changeType": change_type,
                            "item": {"path": file_path},
                            "newContent": ItemContent(
                                content=content_bytes.decode("utf-8"),
                                content_type="rawtext",
                            ),
                        }
                    ],
                )
            ],
            ref_updates=[GitRefUpdate(name=f"refs/heads/{branch}", old_object_id=old_sha)],
        )
        try:
            return self._client.create_push(push, repo_id, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to push file '{file_path}': {e}") from e
