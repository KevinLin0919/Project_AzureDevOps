"""Tests for branch.py — Azure DevOps Branch creation and policies."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.branch import (
    POLICY_COMMENT_REQUIREMENTS,
    POLICY_MERGE_STRATEGY,
    POLICY_WORK_ITEM_LINKING,
    BranchClient,
)
from asgards.tests.conftest import make_service_error

_NULL_SHA = "0000000000000000000000000000000000000000"


@pytest.fixture
def mock_clients():
    with patch("asgards.src.branch._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_git = MagicMock()
        mock_policy = MagicMock()
        mock_conn.clients.get_git_client.return_value = mock_git
        mock_conn.clients.get_policy_client.return_value = mock_policy
        yield mock_git, mock_policy


def test_policy_guid_constants():
    assert len(POLICY_WORK_ITEM_LINKING) == 36
    assert len(POLICY_COMMENT_REQUIREMENTS) == 36
    assert len(POLICY_MERGE_STRATEGY) == 36


def test_create_calls_update_refs_with_null_sha(mock_clients):
    mock_git, _ = mock_clients
    mock_git.get_refs.return_value = [MagicMock(object_id="deadbeef" + "0" * 32)]
    mock_git.update_refs.return_value = [MagicMock()]
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", "repo-id", "feature/new", "main")
    ref_update = mock_git.update_refs.call_args[0][0][0]
    assert ref_update.old_object_id == _NULL_SHA
    assert ref_update.name == "refs/heads/feature/new"


def test_create_resolves_branch_name_to_sha(mock_clients):
    mock_git, _ = mock_clients
    sha = "a" * 40
    mock_git.get_refs.return_value = [MagicMock(object_id=sha)]
    mock_git.update_refs.return_value = [MagicMock()]
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", "repo-id", "feature/new", "main")
    mock_git.get_refs.assert_called_once()
    ref_update = mock_git.update_refs.call_args[0][0][0]
    assert ref_update.new_object_id == sha


def test_create_uses_sha_directly_when_40_hex_chars(mock_clients):
    mock_git, _ = mock_clients
    sha = "b" * 40
    mock_git.update_refs.return_value = [MagicMock()]
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", "repo-id", "feature/from-sha", sha)
    mock_git.get_refs.assert_not_called()
    ref_update = mock_git.update_refs.call_args[0][0][0]
    assert ref_update.new_object_id == sha


def test_create_raises_when_source_ref_not_found(mock_clients):
    mock_git, _ = mock_clients
    mock_git.get_refs.return_value = []
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Source ref 'main' not found"):
        client.create("MyProject", "repo-id", "feature/new", "main")


def test_create_raises_runtime_error_on_update_refs_error(mock_clients):
    mock_git, _ = mock_clients
    mock_git.get_refs.return_value = [MagicMock(object_id="a" * 40)]
    mock_git.update_refs.side_effect = make_service_error("update failed")
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to create branch 'feature/new'"):
        client.create("MyProject", "repo-id", "feature/new", "main")


def test_set_policy_work_item_calls_create_policy(mock_clients):
    mock_git, mock_policy = mock_clients
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_policy_work_item("MyProject", "repo-id", "main")
    config = mock_policy.create_policy_configuration.call_args[0][0]
    assert config.type.id == POLICY_WORK_ITEM_LINKING
    assert config.is_blocking is True
    assert config.is_enabled is True


def test_set_policy_comment_resolution_calls_create_policy(mock_clients):
    mock_git, mock_policy = mock_clients
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_policy_comment_resolution("MyProject", "repo-id", "main")
    config = mock_policy.create_policy_configuration.call_args[0][0]
    assert config.type.id == POLICY_COMMENT_REQUIREMENTS


def test_set_policy_merge_strategy_enforces_no_fast_forward(mock_clients):
    mock_git, mock_policy = mock_clients
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_policy_merge_strategy("MyProject", "repo-id", "main")
    config = mock_policy.create_policy_configuration.call_args[0][0]
    assert config.type.id == POLICY_MERGE_STRATEGY
    settings = config.settings
    assert settings["allowNoFastForward"] is True
    assert settings["allowSquash"] is False
    assert settings["allowRebase"] is False
    assert settings["allowRebaseMerge"] is False


def test_set_all_policies_calls_all_three_setters(mock_clients):
    mock_git, mock_policy = mock_clients
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_all_policies("MyProject", "repo-id", "main")
    assert mock_policy.create_policy_configuration.call_count == 3
    type_ids = [c[0][0].type.id for c in mock_policy.create_policy_configuration.call_args_list]
    assert POLICY_WORK_ITEM_LINKING in type_ids
    assert POLICY_COMMENT_REQUIREMENTS in type_ids
    assert POLICY_MERGE_STRATEGY in type_ids


def test_set_policy_work_item_raises_runtime_error_on_service_error(mock_clients):
    _, mock_policy = mock_clients
    mock_policy.create_policy_configuration.side_effect = make_service_error("policy failed")
    client = BranchClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match=f"Failed to create policy {POLICY_WORK_ITEM_LINKING}"):
        client.set_policy_work_item("MyProject", "repo-id", "main")
