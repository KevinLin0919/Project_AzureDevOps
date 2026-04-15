# Contract: ReleaseClient

**File**: `asgards/src/release.py`
**Import**: `from asgards import ReleaseClient`

```python
class ReleaseClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def get_retention_settings(self, project: str) -> dict: ...
    """
    Returns:
        {
            "days_to_keep_deleted_runs": int,
            "days_to_keep": int,
            "maximum_days_to_keep": int,
            "maximum_runs_to_keep": int,
            "retain_associated_build": bool,
        }
    """

    def set_retention_settings(
        self,
        project: str,
        days_to_keep_deleted_runs: int | None = None,
        days_to_keep: int | None = None,
        maximum_days_to_keep: int | None = None,
        maximum_runs_to_keep: int | None = None,
        retain_associated_build: bool | None = None,
    ) -> None: ...
```

## Behaviour Contracts

- `set_retention_settings()` MUST perform a read-modify-write: fetch current settings,
  update only the non-`None` kwargs, then write back.
- Passing no kwargs to `set_retention_settings()` is a no-op (does not error).
