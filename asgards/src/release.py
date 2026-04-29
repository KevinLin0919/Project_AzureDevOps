"""Azure DevOps Release retention policy operations."""

from azure.devops.exceptions import AzureDevOpsServiceError

from asgards.src._auth import _build_connection


class ReleaseClient:
    """Configure release retention policies and build associations."""

    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None:
        """Initialize the client with explicit credentials or env-var fallbacks."""
        connection = _build_connection(pat, org_url)
        self._client = connection.clients.get_build_client()

    def get_retention_settings(self, project: str) -> dict:
        """Return the current retention settings for the given project.

        Returns a dict with keys:
            days_to_keep_deleted_runs, days_to_keep, maximum_days_to_keep,
            maximum_runs_to_keep, retain_associated_build.
        """
        try:
            settings = self._client.get_build_settings(project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get build settings for '{project}': {e}") from e

        default_policy = settings.default_retention_policy
        maximum_policy = settings.maximum_retention_policy

        return {
            "days_to_keep_deleted_runs": (
                settings.days_to_keep_deleted_builds_before_destroy
            ),
            "days_to_keep": default_policy.days_to_keep if default_policy else None,
            "maximum_days_to_keep": maximum_policy.days_to_keep if maximum_policy else None,
            "maximum_runs_to_keep": maximum_policy.minimum_to_keep if maximum_policy else None,
            "retain_associated_build": (
                not default_policy.delete_build_record if default_policy else None
            ),
        }

    def set_retention_settings(
        self,
        project: str,
        days_to_keep_deleted_runs: int | None = None,
        days_to_keep: int | None = None,
        maximum_days_to_keep: int | None = None,
        maximum_runs_to_keep: int | None = None,
        retain_associated_build: bool | None = None,
    ) -> None:
        """Partially update retention settings (read-modify-write).

        Only the provided (non-None) keyword arguments are updated.
        """
        if all(
            value is None
            for value in (
                days_to_keep_deleted_runs,
                days_to_keep,
                maximum_days_to_keep,
                maximum_runs_to_keep,
                retain_associated_build,
            )
        ):
            return

        try:
            settings = self._client.get_build_settings(project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to get build settings for '{project}': {e}") from e

        if days_to_keep_deleted_runs is not None:
            settings.days_to_keep_deleted_builds_before_destroy = days_to_keep_deleted_runs

        if settings.default_retention_policy:
            if days_to_keep is not None:
                settings.default_retention_policy.days_to_keep = days_to_keep
            if retain_associated_build is not None:
                settings.default_retention_policy.delete_build_record = (
                    not retain_associated_build
                )

        if settings.maximum_retention_policy:
            if maximum_days_to_keep is not None:
                settings.maximum_retention_policy.days_to_keep = maximum_days_to_keep
            if maximum_runs_to_keep is not None:
                settings.maximum_retention_policy.minimum_to_keep = maximum_runs_to_keep

        try:
            self._client.update_build_settings(settings, project)
        except AzureDevOpsServiceError as e:
            raise RuntimeError(f"Failed to update build settings for '{project}': {e}") from e
