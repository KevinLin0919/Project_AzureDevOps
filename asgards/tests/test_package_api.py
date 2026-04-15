"""Tests for the package-level public API."""

from asgards import (
    BranchClient,
    MemberClient,
    PipelineClient,
    ProjectClient,
    ReleaseClient,
    RepoClient,
)


def test_top_level_package_exports_all_clients():
    assert ProjectClient.__name__ == "ProjectClient"
    assert RepoClient.__name__ == "RepoClient"
    assert MemberClient.__name__ == "MemberClient"
    assert PipelineClient.__name__ == "PipelineClient"
    assert ReleaseClient.__name__ == "ReleaseClient"
    assert BranchClient.__name__ == "BranchClient"
