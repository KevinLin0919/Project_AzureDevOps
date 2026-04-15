# Contract: BranchClient

**File**: `asgards/src/branch.py`
**Import**: `from asgards import BranchClient`

```python
# Well-known Azure DevOps policy type GUIDs (verify via policy_client.get_policy_types())
POLICY_WORK_ITEM_LINKING    = "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e"
POLICY_COMMENT_REQUIREMENTS = "c6a1889d-b943-4856-b76f-9e46bb6b0df3"
POLICY_MERGE_STRATEGY       = "fa4e907d-c16b-452d-8106-7efa0cb84489"

class BranchClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def create(
        self,
        project: str,
        repo_id: str,
        branch_name: str,
        source_ref: str,          # branch name (e.g. "main") or full commit SHA
    ) -> GitRef: ...

    def set_policy_work_item(
        self,
        project: str,
        repo_id: str,
        branch_name: str,
    ) -> PolicyConfiguration: ...

    def set_policy_comment_resolution(
        self,
        project: str,
        repo_id: str,
        branch_name: str,
    ) -> PolicyConfiguration: ...

    def set_policy_merge_strategy(
        self,
        project: str,
        repo_id: str,
        branch_name: str,
    ) -> PolicyConfiguration: ...

    def set_all_policies(
        self,
        project: str,
        repo_id: str,
        branch_name: str,
    ) -> None: ...
```

## Behaviour Contracts

- `create()` MUST resolve `source_ref` to a commit SHA if it is a branch name.
- `set_policy_merge_strategy()` MUST configure `allowNoFastForward=True` and all other
  merge modes (`allowSquash`, `allowRebase`, `allowRebaseMerge`) as `False`.
- All policies are created with `is_blocking=True` and `is_enabled=True`.
- `set_all_policies()` calls the three individual setters in sequence.
