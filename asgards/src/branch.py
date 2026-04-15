"""Azure DevOps Branch creation and policy enforcement operations."""

from azure.devops.exceptions import AzureDevOpsServiceError
from azure.devops.v7_1.git.models import GitRefUpdate
from azure.devops.v7_1.policy.models import PolicyConfiguration, PolicyType

from asgards.src._auth import _build_connection

POLICY_WORK_ITEM_LINKING = "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e"
POLICY_COMMENT_REQUIREMENTS = "c6a1889d-b943-4856-b76f-9e46bb6b0df3"
POLICY_MERGE_STRATEGY = "fa4e907d-c16b-452d-8106-7efa0cb84489"

_NULL_SHA = "0000000000000000000000000000000000000000"


class BranchClient:
    """Create branches and set branch policies (work item, comment, merge strategy)."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client with explicit credentials or env-var fallbacks."""
        connection = _build_connection(pat, org_url)
        self._git_client = connection.clients.get_git_client()
        self._policy_client = connection.clients.get_policy_client()

    def _resolve_ref_to_sha(self, repo_id: str, project: str, source_ref: str) -> str:
        """Resolve a branch name to a commit SHA or return the SHA unchanged."""
        if len(source_ref) == 40 and all(c in "0123456789abcdefABCDEF" for c in source_ref):
            return source_ref
        refs = self._git_client.get_refs(repo_id, project, filter=f"heads/{source_ref}")
        if not refs:
            raise RuntimeError(f"Source ref '{source_ref}' not found in repo '{repo_id}'")
        return refs[0].object_id

    def create(self, project: str, repo_id: str, branch_name: str, source_ref: str):
        """Create a new branch from a source ref (branch name or commit SHA)."""
        sha = self._resolve_ref_to_sha(repo_id, project, source_ref)
        ref_update = GitRefUpdate(
            name=f"refs/heads/{branch_name}",
            old_object_id=_NULL_SHA,
            new_object_id=sha,
        )
        try:
            results = self._git_client.update_refs([ref_update], repo_id, project)
            return results[0] if results else None
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {e}") from e

    def _create_policy(self, project: str, type_id: str, settings: dict):
        """Create a branch policy configuration."""
        config = PolicyConfiguration(
            type=PolicyType(id=type_id),
            is_enabled=True,
            is_blocking=True,
            settings=settings,
        )
        try:
            return self._policy_client.create_policy_configuration(config, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to create policy {type_id}: {e}") from e

    def _branch_scope(self, repo_id: str, branch_name: str) -> list:
        return [
            {
                "refName": f"refs/heads/{branch_name}",
                "matchKind": "Exact",
                "repositoryId": repo_id,
            }
        ]

    def set_policy_work_item(self, project: str, repo_id: str, branch_name: str):
        """Require linked work item on PRs targeting this branch."""
        return self._create_policy(
            project,
            POLICY_WORK_ITEM_LINKING,
            {"scope": self._branch_scope(repo_id, branch_name)},
        )

    def set_policy_comment_resolution(self, project: str, repo_id: str, branch_name: str):
        """Require all PR comments to be resolved before merge."""
        return self._create_policy(
            project,
            POLICY_COMMENT_REQUIREMENTS,
            {"scope": self._branch_scope(repo_id, branch_name)},
        )

    def set_policy_merge_strategy(self, project: str, repo_id: str, branch_name: str):
        """Enforce Basic merge (no fast-forward) as the only allowed merge strategy."""
        return self._create_policy(
            project,
            POLICY_MERGE_STRATEGY,
            {
                "allowSquash": False,
                "allowNoFastForward": True,
                "allowRebase": False,
                "allowRebaseMerge": False,
                "scope": self._branch_scope(repo_id, branch_name),
            },
        )

    def set_all_policies(self, project: str, repo_id: str, branch_name: str) -> None:
        """Apply all three branch policies: work item, comment resolution, merge strategy."""
        self.set_policy_work_item(project, repo_id, branch_name)
        self.set_policy_comment_resolution(project, repo_id, branch_name)
        self.set_policy_merge_strategy(project, repo_id, branch_name)
