"""Tests for release.py — Azure DevOps Release retention policy."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.release import ReleaseClient
from asgards.tests.conftest import make_service_error


@pytest.fixture
def mock_build():
    with patch("asgards.src.release._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_client = MagicMock()
        mock_conn.clients.get_build_client.return_value = mock_client
        yield mock_client


def _make_settings(
    deleted_days=7,
    default_days=30,
    max_days=365,
    max_runs=10,
    delete_build_record=False,
):
    default_policy = MagicMock(
        days_to_keep=default_days,
        delete_build_record=delete_build_record,
    )
    max_policy = MagicMock(days_to_keep=max_days, minimum_to_keep=max_runs)
    settings = MagicMock(
        days_to_keep_deleted_builds_before_destroy=deleted_days,
        default_retention_policy=default_policy,
        maximum_retention_policy=max_policy,
    )
    return settings


def test_get_retention_settings_returns_five_keys(mock_build):
    mock_build.get_build_settings.return_value = _make_settings()
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.get_retention_settings("MyProject")
    assert set(result.keys()) == {
        "days_to_keep_deleted_runs",
        "days_to_keep",
        "maximum_days_to_keep",
        "maximum_runs_to_keep",
        "retain_associated_build",
    }


def test_get_retention_settings_maps_fields_correctly(mock_build):
    mock_build.get_build_settings.return_value = _make_settings(
        deleted_days=3,
        default_days=14,
        max_days=180,
        max_runs=5,
        delete_build_record=False,
    )
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.get_retention_settings("MyProject")
    assert result["days_to_keep_deleted_runs"] == 3
    assert result["days_to_keep"] == 14
    assert result["maximum_days_to_keep"] == 180
    assert result["maximum_runs_to_keep"] == 5
    assert result["retain_associated_build"] is True


def test_get_retention_settings_raises_runtime_error_on_service_error(mock_build):
    mock_build.get_build_settings.side_effect = make_service_error("settings failed")
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get build settings"):
        client.get_retention_settings("MyProject")


def test_set_retention_settings_reads_before_writing(mock_build):
    mock_build.get_build_settings.return_value = _make_settings()
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_retention_settings("MyProject", days_to_keep=60)
    mock_build.get_build_settings.assert_called_once_with("MyProject")
    mock_build.update_build_settings.assert_called_once()


def test_set_retention_settings_updates_only_provided_kwarg(mock_build):
    settings = _make_settings(deleted_days=7, default_days=30)
    mock_build.get_build_settings.return_value = settings
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_retention_settings("MyProject", days_to_keep=99)
    assert settings.default_retention_policy.days_to_keep == 99
    assert settings.days_to_keep_deleted_builds_before_destroy == 7


def test_set_retention_settings_updates_build_record_flag(mock_build):
    mock_build.get_build_settings.return_value = _make_settings()
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_retention_settings("MyProject", retain_associated_build=False)
    settings = mock_build.get_build_settings.return_value
    assert settings.default_retention_policy.delete_build_record is True
    mock_build.update_build_settings.assert_called_once()


def test_set_retention_settings_updates_deleted_and_maximum_values(mock_build):
    settings = _make_settings()
    mock_build.get_build_settings.return_value = settings
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_retention_settings(
        "MyProject",
        days_to_keep_deleted_runs=9,
        maximum_days_to_keep=180,
        maximum_runs_to_keep=7,
    )
    assert settings.days_to_keep_deleted_builds_before_destroy == 9
    assert settings.maximum_retention_policy.days_to_keep == 180
    assert settings.maximum_retention_policy.minimum_to_keep == 7


def test_set_retention_settings_raises_runtime_error_on_read_error(mock_build):
    mock_build.get_build_settings.side_effect = make_service_error("read failed")
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to get build settings"):
        client.set_retention_settings("MyProject", days_to_keep=10)


def test_set_retention_settings_raises_runtime_error_on_update_error(mock_build):
    mock_build.get_build_settings.return_value = _make_settings()
    mock_build.update_build_settings.side_effect = make_service_error("update failed")
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to update build settings"):
        client.set_retention_settings("MyProject", days_to_keep=10)


def test_set_retention_settings_no_kwargs_is_noop(mock_build):
    client = ReleaseClient(pat="x", org_url="https://dev.azure.com/org")
    client.set_retention_settings("MyProject")
    mock_build.get_build_settings.assert_not_called()
    mock_build.update_build_settings.assert_not_called()
