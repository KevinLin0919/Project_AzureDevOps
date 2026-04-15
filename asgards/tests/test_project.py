"""Tests for project.py — Azure DevOps Project management."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.project import PROCESS_TEMPLATE_IDS, ProjectClient
from asgards.tests.conftest import make_service_error


@pytest.fixture
def mock_core():
    with patch("asgards.src.project._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_client = MagicMock()
        mock_conn.clients.get_core_client.return_value = mock_client
        yield mock_client


def test_create_calls_queue_create_project(mock_core):
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject")
    mock_core.queue_create_project.assert_called_once()


def test_create_maps_named_process_template_to_guid(mock_core):
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", process_template="Agile")
    project_arg = mock_core.queue_create_project.call_args[0][0]
    assert (
        project_arg.capabilities["processTemplate"]["templateTypeId"]
        == PROCESS_TEMPLATE_IDS["agile"]
    )


def test_create_keeps_custom_process_template_guid(mock_core):
    template_guid = "11111111-2222-3333-4444-555555555555"
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    client.create("MyProject", process_template=template_guid)
    project_arg = mock_core.queue_create_project.call_args[0][0]
    assert project_arg.capabilities["processTemplate"]["templateTypeId"] == template_guid


def test_create_raises_runtime_error_on_service_error(mock_core):
    mock_core.queue_create_project.side_effect = make_service_error("error")
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to create project"):
        client.create("Bad")


def test_get_calls_get_project(mock_core):
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    client.get("MyProject")
    mock_core.get_project.assert_called_once_with("MyProject")


def test_get_raises_runtime_error_on_service_error(mock_core):
    mock_core.get_project.side_effect = make_service_error("not found", status_code=500)
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get project"):
        client.get("Missing")


def test_list_calls_get_projects(mock_core):
    mock_core.get_projects.return_value = []
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.list()
    mock_core.get_projects.assert_called_once()
    assert result == []


def test_delete_calls_queue_delete_project(mock_core):
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    client.delete("proj-id-123")
    mock_core.queue_delete_project.assert_called_once_with("proj-id-123")


def test_list_raises_runtime_error_on_service_error(mock_core):
    mock_core.get_projects.side_effect = make_service_error("list failed")
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list projects"):
        client.list()


def test_delete_raises_runtime_error_on_service_error(mock_core):
    mock_core.queue_delete_project.side_effect = make_service_error("delete failed")
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to delete project"):
        client.delete("proj-id-123")


def test_exists_returns_true_when_project_found(mock_core):
    mock_core.get_project.return_value = MagicMock()
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.exists("MyProject") is True


def test_exists_returns_false_on_service_error(mock_core):
    mock_core.get_project.side_effect = make_service_error("404 not found", status_code=404)
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.exists("Missing") is False


def test_exists_raises_runtime_error_on_non_404_service_error(mock_core):
    mock_core.get_project.side_effect = make_service_error("boom", status_code=500)
    client = ProjectClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to check project"):
        client.exists("Broken")
