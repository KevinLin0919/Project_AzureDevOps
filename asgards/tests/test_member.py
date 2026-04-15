"""Tests for member.py — Azure DevOps Team and member management."""
from unittest.mock import MagicMock, patch

import pytest

from asgards.src.member import GROUP_CONTRIBUTORS, GROUP_PROJECT_ADMINISTRATORS, MemberClient
from asgards.tests.conftest import make_service_error


@pytest.fixture
def mock_graph():
    with patch("asgards.src.member._build_connection") as mock_auth:
        mock_conn = MagicMock()
        mock_auth.return_value = mock_conn
        mock_client = MagicMock()
        mock_conn.clients.get_graph_client.return_value = mock_client
        yield mock_client


def _make_group(display_name: str) -> MagicMock:
    group = MagicMock()
    group.display_name = display_name
    group.descriptor = f"descriptor-{display_name}"
    return group


def test_group_name_constants():
    assert GROUP_PROJECT_ADMINISTRATORS == "Project Administrators"
    assert GROUP_CONTRIBUTORS == "Contributors"


def test_find_group_returns_matching_group(mock_graph):
    group = _make_group("Project Administrators")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group, _make_group("Other")])
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.find_group("proj-id", "Project Administrators")
    assert result.display_name == "Project Administrators"


def test_find_group_raises_when_not_found(mock_graph):
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[_make_group("Contributors")])
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="not found"):
        client.find_group("proj-id", "Admins")


def test_find_group_raises_runtime_error_on_service_error(mock_graph):
    mock_graph.get_descriptor.side_effect = make_service_error("group failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to find group"):
        client.find_group("proj-id", "Contributors")


def test_add_calls_add_member_to_group(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    user = MagicMock(mail_address="alice@example.com", descriptor="user-desc")
    mock_graph.list_users.return_value = MagicMock(value=[user])
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    client.add("proj-id", "Contributors", "alice@example.com")
    mock_graph.add_membership.assert_called_once_with("user-desc", group.descriptor)


def test_add_uses_continuation_token_to_find_user_on_later_page(mock_graph):
    group = _make_group("Contributors")
    first_page = MagicMock(value=[], continuation_token="next-page")
    user = MagicMock(mail_address="alice@example.com", descriptor="user-desc")
    second_page = MagicMock(value=[user], continuation_token=None)
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    mock_graph.list_users.side_effect = [first_page, second_page]
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    client.add("proj-id", "Contributors", "alice@example.com")
    assert mock_graph.list_users.call_count == 2
    mock_graph.list_users.assert_any_call(continuation_token=None)
    mock_graph.list_users.assert_any_call(continuation_token="next-page")


def test_add_raises_runtime_error_when_user_not_found(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    mock_graph.list_users.return_value = MagicMock(value=[])
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="User 'alice@example.com' not found"):
        client.add("proj-id", "Contributors", "alice@example.com")


def test_add_raises_runtime_error_when_list_users_fails(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    mock_graph.list_users.side_effect = make_service_error("user lookup failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list users"):
        client.add("proj-id", "Contributors", "alice@example.com")


def test_add_raises_runtime_error_on_membership_error(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    user = MagicMock(mail_address="alice@example.com", descriptor="user-desc")
    mock_graph.list_users.return_value = MagicMock(value=[user])
    mock_graph.add_membership.side_effect = make_service_error("add failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to add 'alice@example.com'"):
        client.add("proj-id", "Contributors", "alice@example.com")


def test_remove_calls_remove_member_from_group(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    user = MagicMock(mail_address="bob@example.com", descriptor="user-desc-bob")
    mock_graph.list_users.return_value = MagicMock(value=[user])
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    client.remove("proj-id", "Contributors", "bob@example.com")
    mock_graph.remove_membership.assert_called_once_with("user-desc-bob", group.descriptor)


def test_remove_raises_runtime_error_on_membership_error(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    user = MagicMock(mail_address="bob@example.com", descriptor="user-desc-bob")
    mock_graph.list_users.return_value = MagicMock(value=[user])
    mock_graph.remove_membership.side_effect = make_service_error("remove failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to remove 'bob@example.com'"):
        client.remove("proj-id", "Contributors", "bob@example.com")


def test_list_members_calls_list_memberships(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    membership_1 = MagicMock(member_descriptor="user-1")
    membership_2 = MagicMock(member_descriptor="user-2")
    user_1 = MagicMock(principal_name="alice@example.com")
    user_2 = MagicMock(principal_name="bob@example.com")
    mock_graph.list_memberships.return_value = [membership_1, membership_2]
    mock_graph.get_user.side_effect = [user_1, user_2]
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    result = client.list_members("proj-id", "Contributors")
    mock_graph.list_memberships.assert_called_once_with(group.descriptor, direction="down")
    mock_graph.get_user.assert_any_call("user-1")
    mock_graph.get_user.assert_any_call("user-2")
    assert len(result) == 2
    assert result[0].principal_name == "alice@example.com"


def test_list_members_raises_runtime_error_on_service_error(mock_graph):
    group = _make_group("Contributors")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    mock_graph.list_memberships.side_effect = make_service_error("list failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list members of 'Contributors'"):
        client.list_members("proj-id", "Contributors")


def test_list_members_raises_runtime_error_when_member_lookup_fails(mock_graph):
    group = _make_group("Contributors")
    membership = MagicMock(member_descriptor="user-1")
    mock_graph.get_descriptor.return_value = MagicMock(value="scope-descriptor")
    mock_graph.list_groups.return_value = MagicMock(value=[group])
    mock_graph.list_memberships.return_value = [membership]
    mock_graph.get_user.side_effect = make_service_error("lookup failed")
    client = MemberClient(pat="x", org_url="https://dev.azure.com/org")
    with pytest.raises(RuntimeError, match="Failed to list members of 'Contributors'"):
        client.list_members("proj-id", "Contributors")
