# Contract: RepoClient

**File**: `asgards/src/repo.py`
**Import**: `from asgards import RepoClient`

```python
FILE_SIZE_LIMIT_BYTES: int = 5 * 1024 * 1024  # module-level constant

class RepoClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None) -> None: ...

    def create(self, project: str, name: str) -> GitRepository: ...

    def get(self, project: str, repo_id_or_name: str) -> GitRepository: ...

    def list(self, project: str) -> list[GitRepository]: ...

    def delete(self, project: str, repo_id: str) -> None: ...

    def get_file_content(
        self,
        project: str,
        repo_id: str,
        file_path: str,
        branch: str = "main",
    ) -> str: ...

    def get_file_content_from_source(
        self,
        src_org_url: str,
        src_pat: str,
        src_project: str,
        src_repo: str,
        file_path: str,
        branch: str = "main",
    ) -> str: ...

    def push_file(
        self,
        project: str,
        repo_id: str,
        file_path: str,
        content: str | bytes,
        branch: str = "main",
        commit_message: str = "chore: update file via asgards",
    ) -> GitPush: ...
```

## Behaviour Contracts

- `push_file()` MUST raise `ValueError` before any API call if `content` exceeds 5 MB.
- `push_file()` MUST detect add vs update by calling `get_item()` first.
- `get_file_content_from_source()` uses a separate `Connection` built with `src_pat`/`src_org_url`.
