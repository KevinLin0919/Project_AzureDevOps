# Contract: PipelineClient

**File**: `asgards/src/pipeline.py`
**Import**: `from asgards import PipelineClient`

```python
class PipelineClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def create_from_yaml(
        self,
        project: str,
        name: str,
        repo_id: str,
        yaml_path: str,
        default_branch: str = "main",
    ) -> BuildDefinition: ...

    def list(self, project: str) -> list[BuildDefinitionReference]: ...

    def trigger(self, project: str, definition_id: int) -> Build: ...

    def get_run_status(self, project: str, build_id: int) -> str: ...
```

## Behaviour Contracts

- `get_run_status()` MUST return one of: `"queued"`, `"running"`, `"succeeded"`,
  `"failed"`, `"canceled"`. Never return the raw SDK enum value.
- `create_from_yaml()` uses process type `2` (YAML pipeline) in the `BuildDefinition`.
