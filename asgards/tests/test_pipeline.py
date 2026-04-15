"""Tests for pipeline.py — Azure DevOps Pipeline configuration."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.pipeline import PipelineClient
from asgards.tests.conftest import make_service_error


@pytest.fixture
def mock_build():
    with patch("asgards.src.pipeline._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_client = MagicMock()
        mock_conn.clients.get_build_client.return_value = mock_client
        yield mock_client


def test_create_from_yaml_uses_type_2(mock_build):
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    client.create_from_yaml("MyProject", "CI", "repo-id", "/pipelines/main.yml")
    definition_arg = mock_build.create_definition.call_args[0][0]
    assert definition_arg.process["type"] == 2
    assert definition_arg.process["yamlFilename"] == "/pipelines/main.yml"


def test_create_from_yaml_raises_on_error(mock_build):
    mock_build.create_definition.side_effect = make_service_error("error")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to create pipeline"):
        client.create_from_yaml("P", "CI", "r", "/p.yml")


def test_list_calls_get_definitions(mock_build):
    mock_build.get_definitions.return_value = []
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.list("MyProject")
    mock_build.get_definitions.assert_called_once_with("MyProject")
    assert result == []


def test_list_raises_runtime_error_on_service_error(mock_build):
    mock_build.get_definitions.side_effect = make_service_error("list failed")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list pipelines"):
        client.list("MyProject")


def test_trigger_calls_queue_build(mock_build):
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    client.trigger("MyProject", 42)
    mock_build.queue_build.assert_called_once()
    build_arg = mock_build.queue_build.call_args[0][0]
    assert build_arg.definition["id"] == 42


def test_trigger_raises_runtime_error_on_service_error(mock_build):
    mock_build.queue_build.side_effect = make_service_error("queue failed")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to trigger pipeline 42"):
        client.trigger("MyProject", 42)


def test_get_run_status_queued_for_not_started(mock_build):
    mock_build.get_build.return_value = MagicMock(status="notStarted", result=None)
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "queued"
    mock_build.get_build.assert_called_once_with("MyProject", 1)


def test_get_run_status_queued_for_postponed(mock_build):
    mock_build.get_build.return_value = MagicMock(status="postponed", result=None)
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "queued"


def test_get_run_status_running_for_in_progress(mock_build):
    mock_build.get_build.return_value = MagicMock(status="inProgress", result=None)
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "running"


def test_get_run_status_succeeded_for_completed_succeeded(mock_build):
    mock_build.get_build.return_value = MagicMock(status="completed", result="succeeded")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "succeeded"


def test_get_run_status_failed_for_completed_failed(mock_build):
    mock_build.get_build.return_value = MagicMock(status="completed", result="failed")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "failed"


def test_get_run_status_canceled_for_completed_canceled(mock_build):
    mock_build.get_build.return_value = MagicMock(status="completed", result="canceled")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "canceled"


def test_get_run_status_defaults_to_failed_for_unknown_completed_result(mock_build):
    mock_build.get_build.return_value = MagicMock(status="completed", result="weird")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "failed"


def test_get_run_status_defaults_to_queued_for_unknown_status(mock_build):
    mock_build.get_build.return_value = MagicMock(status="mystery", result=None)
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    assert client.get_run_status("MyProject", 1) == "queued"


def test_get_run_status_raises_runtime_error_on_service_error(mock_build):
    mock_build.get_build.side_effect = make_service_error("build failed")
    client = PipelineClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get build 1"):
        client.get_run_status("MyProject", 1)
