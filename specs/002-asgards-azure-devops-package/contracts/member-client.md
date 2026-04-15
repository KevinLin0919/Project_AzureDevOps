# Contract: MemberClient

**File**: `asgards/src/member.py`
**Import**: `from asgards import MemberClient`

```python
GROUP_PROJECT_ADMINISTRATORS: str = "Project Administrators"  # module-level constant
GROUP_CONTRIBUTORS: str = "Contributors"                       # module-level constant

class MemberClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def find_group(
        self,
        project_id: str,
        group_display_name: str,
    ) -> GraphGroup: ...

    def add(
        self,
        project_id: str,
        group_display_name: str,
        user_email: str,
    ) -> None: ...

    def remove(
        self,
        project_id: str,
        group_display_name: str,
        user_email: str,
    ) -> None: ...

    def list_members(
        self,
        project_id: str,
        group_display_name: str,
    ) -> list[GraphMember]: ...
```

## Behaviour Contracts

- `find_group()` MUST raise `RuntimeError` if no group matches `group_display_name`.
- `add()` / `remove()` resolve the group descriptor internally via `find_group()`.
