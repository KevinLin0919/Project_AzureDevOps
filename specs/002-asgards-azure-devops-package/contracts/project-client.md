# Contract: ProjectClient

**File**: `asgards/src/project.py`
**Import**: `from asgards import ProjectClient`

```python
class ProjectClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def create(
        self,
        name: str,
        description: str = "",
        process_template: str = "Agile",
    ) -> OperationReference: ...

    def get(self, project_id_or_name: str) -> TeamProject: ...

    def list(self) -> list[TeamProjectReference]: ...

    def delete(self, project_id: str) -> OperationReference: ...

    def exists(self, name: str) -> bool: ...
```

## Behaviour Contracts

- `exists()` MUST return `False` (not raise) when the project is not found.
- `create()` and `delete()` return an `OperationReference`; they do not block until completion.
- `get()` MUST raise `RuntimeError` if the project does not exist.
