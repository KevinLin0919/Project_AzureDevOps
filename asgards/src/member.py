"""Azure DevOps Team and member management operations."""

from azure.devops.exceptions import AzureDevOpsServiceError

from asgards.src._auth import _build_connection

GROUP_PROJECT_ADMINISTRATORS = "Project Administrators"
GROUP_CONTRIBUTORS = "Contributors"


class MemberClient:
    """Add, remove, and list members within Azure DevOps teams/groups."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client with explicit credentials or env-var fallbacks."""
        connection = _build_connection(pat, org_url)
        self._graph_client = connection.clients.get_graph_client()

    def find_group(self, project_id: str, group_display_name: str):
        """Find a group by display name within a project scope.

        Raises:
            RuntimeError: If no group matching group_display_name is found.
        """
        try:
            descriptor = self._graph_client.get_descriptor(project_id)
            groups = self._graph_client.list_groups(scope_descriptor=descriptor.value)
            for group in groups.value or []:
                if group.display_name == group_display_name:
                    return group
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to find group '{group_display_name}': {e}") from e
        raise RuntimeError(f"Group '{group_display_name}' not found in project '{project_id}'")

    def _get_user_descriptor(self, user_email: str) -> str:
        """Look up a user's graph descriptor by email or principal name."""
        continuation_token = None
        try:
            while True:
                result = self._graph_client.list_users(continuation_token=continuation_token)
                for user in result.value or []:
                    if user.mail_address == user_email or user.principal_name == user_email:
                        return user.descriptor
                continuation_token = getattr(result, "continuation_token", None)
                if not isinstance(continuation_token, str) or not continuation_token:
                    break
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to list users: {e}") from e
        raise RuntimeError(f"User '{user_email}' not found in the organization")

    def add(self, project_id: str, group_display_name: str, user_email: str) -> None:
        """Add a user (by email) to the named group in the given project."""
        group = self.find_group(project_id, group_display_name)
        user_descriptor = self._get_user_descriptor(user_email)
        try:
            self._graph_client.add_membership(user_descriptor, group.descriptor)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(
                f"Failed to add '{user_email}' to '{group_display_name}': {e}"
            ) from e

    def remove(self, project_id: str, group_display_name: str, user_email: str) -> None:
        """Remove a user (by email) from the named group in the given project."""
        group = self.find_group(project_id, group_display_name)
        user_descriptor = self._get_user_descriptor(user_email)
        try:
            self._graph_client.remove_membership(user_descriptor, group.descriptor)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(
                f"Failed to remove '{user_email}' from '{group_display_name}': {e}"
            ) from e

    def list_members(self, project_id: str, group_display_name: str) -> list:
        """List all members of the named group in the given project."""
        group = self.find_group(project_id, group_display_name)
        try:
            memberships = self._graph_client.list_memberships(group.descriptor, direction="down")
            members = []
            for membership in memberships or []:
                members.append(self._graph_client.get_user(membership.member_descriptor))
            return members
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to list members of '{group_display_name}': {e}") from e
