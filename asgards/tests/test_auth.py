"""Tests for _auth.py — shared authentication helper."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src._auth import _build_connection


def test_missing_pat_raises_value_error(monkeypatch):
    monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
    monkeypatch.delenv("AZURE_DEVOPS_ORG_URL", raising=False)
    with pytest.raises(ValueError, match="PAT required"):
        _build_connection(None, "https://dev.azure.com/org")


def test_missing_org_url_raises_value_error(monkeypatch):
    monkeypatch.delenv("AZURE_DEVOPS_ORG_URL", raising=False)
    with pytest.raises(ValueError, match="Org URL required"):
        _build_connection("my-pat", None)


def test_env_var_fallback(monkeypatch):
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "env-pat")
    monkeypatch.setenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/org")
    with patch("asgards.src._auth.Connection") as mock_conn:
        _build_connection(None, None)
        mock_conn.assert_called_once()


def test_constructor_arg_overrides_env_var(monkeypatch):
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "env-pat")
    monkeypatch.setenv("AZURE_DEVOPS_ORG_URL", "https://dev.azure.com/env-org")
    with patch("asgards.src._auth.Connection") as mock_conn:
        _build_connection("explicit-pat", "https://dev.azure.com/explicit-org")
        call_kwargs = mock_conn.call_args[1]
        assert call_kwargs.get("base_url") == "https://dev.azure.com/explicit-org"


def test_returns_connection_instance(monkeypatch):
    monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
    monkeypatch.delenv("AZURE_DEVOPS_ORG_URL", raising=False)
    with patch("asgards.src._auth.Connection") as mock_conn:
        mock_conn.return_value = MagicMock()
        result = _build_connection("pat", "https://dev.azure.com/org")
        assert result is mock_conn.return_value
