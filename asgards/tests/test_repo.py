"""Tests for repo.py — Azure DevOps Repository operations."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.repo import FILE_SIZE_LIMIT_BYTES, RepoClient
from asgards.tests.conftest import make_service_error


@pytest.fixture
def mock_git():
    with patch("asgards.src.repo._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_client = MagicMock()
        mock_conn.clients.get_git_client.return_value = mock_client
        yield mock_client


def test_create_calls_create_repository(mock_git):
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", "my-repo")
    mock_git.create_repository.assert_called_once()


def test_create_raises_runtime_error_on_service_error(mock_git):
    mock_git.create_repository.side_effect = make_service_error("create failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to create repo"):
        client.create("MyProject", "my-repo")


def test_get_calls_get_repository(mock_git):
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    client.get("MyProject", "my-repo")
    mock_git.get_repository.assert_called_once_with("my-repo", "MyProject")


def test_get_raises_runtime_error_on_service_error(mock_git):
    mock_git.get_repository.side_effect = make_service_error("get failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get repo"):
        client.get("MyProject", "my-repo")


def test_list_calls_get_repositories(mock_git):
    mock_git.get_repositories.return_value = []
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.list("MyProject")
    mock_git.get_repositories.assert_called_once_with("MyProject")
    assert result == []


def test_list_raises_runtime_error_on_service_error(mock_git):
    mock_git.get_repositories.side_effect = make_service_error("list failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list repos"):
        client.list("MyProject")


def test_delete_calls_delete_repository(mock_git):
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    client.delete("MyProject", "repo-id-123")
    mock_git.delete_repository.assert_called_once_with("repo-id-123", "MyProject")


def test_delete_raises_runtime_error_on_service_error(mock_git):
    mock_git.delete_repository.side_effect = make_service_error("delete failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to delete repo"):
        client.delete("MyProject", "repo-id-123")


def test_get_file_content_calls_get_item_content(mock_git):
    mock_git.get_item_content.return_value = [b"hello ", b"world"]
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.get_file_content("MyProject", "repo-id", "/README.md")
    mock_git.get_item_content.assert_called_once()
    assert result == "hello world"


def test_get_file_content_raises_runtime_error_on_service_error(mock_git):
    mock_git.get_item_content.side_effect = make_service_error("read failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get file"):
        client.get_file_content("MyProject", "repo-id", "/README.md")


def test_get_file_content_from_source_builds_separate_connection():
    with patch("asgards.src.repo._build_connection") as mock_auth:
        mock_own_conn = MagicMock()
        mock_src_conn = MagicMock()
        mock_auth.side_effect = [mock_own_conn, mock_src_conn]
        mock_own_conn.clients.get_git_client.return_value = MagicMock()
        mock_src_client = MagicMock()
        mock_src_client.get_item_content.return_value = [b"src content"]
        mock_src_conn.clients.get_git_client.return_value = mock_src_client

        client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
        result = client.get_file_content_from_source(
            "https://dev.azure.com/other",
            "other-pat",
            "SrcProject",
            "src-repo",
            "/config.yml",
        )
        assert mock_auth.call_count == 2
        mock_src_client.get_item_content.assert_called_once()
        assert result == "src content"


def test_get_file_content_from_source_raises_runtime_error():
    with patch("asgards.src.repo._build_connection") as mock_auth:
        mock_own_conn = MagicMock()
        mock_src_conn = MagicMock()
        mock_auth.side_effect = [mock_own_conn, mock_src_conn]
        mock_own_conn.clients.get_git_client.return_value = MagicMock()
        mock_src_client = MagicMock()
        mock_src_client.get_item_content.side_effect = make_service_error("read failed")
        mock_src_conn.clients.get_git_client.return_value = mock_src_client

        client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
        with pytest.raises(RuntimeError, match="Failed to get file '/config.yml' from source"):
            client.get_file_content_from_source(
                "https://dev.azure.com/other",
                "other-pat",
                "SrcProject",
                "src-repo",
                "/config.yml",
            )


def test_push_file_raises_value_error_when_content_exceeds_5mb(mock_git):
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    oversized = "x" * (FILE_SIZE_LIMIT_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds the 5 MB limit"):
        client.push_file("MyProject", "repo-id", "/big.txt", oversized)
    mock_git.create_push.assert_not_called()


def test_push_file_uses_add_for_new_file(mock_git):
    mock_git.get_item.side_effect = make_service_error("not found", status_code=404)
    mock_git.get_refs.return_value = [MagicMock(object_id="abc123")]
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    client.push_file("MyProject", "repo-id", "/new.txt", "content")
    push_arg = mock_git.create_push.call_args[0][0]
    assert push_arg.commits[0].changes[0]["changeType"] == 1


def test_push_file_uses_edit_for_existing_file(mock_git):
    mock_git.get_item.return_value = MagicMock()
    mock_git.get_refs.return_value = [MagicMock(object_id="abc123")]
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    client.push_file("MyProject", "repo-id", "/existing.txt", "updated content")
    push_arg = mock_git.create_push.call_args[0][0]
    assert push_arg.commits[0].changes[0]["changeType"] == 2


def test_push_file_raises_runtime_error_when_create_push_fails(mock_git):
    mock_git.get_item.return_value = MagicMock()
    mock_git.get_refs.return_value = [MagicMock(object_id="abc123")]
    mock_git.create_push.side_effect = make_service_error("push failed")
    client = RepoClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to push file"):
        client.push_file("MyProject", "repo-id", "/existing.txt", "updated content")
