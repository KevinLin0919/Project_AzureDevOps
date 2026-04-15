# Data Model: Asgards — Azure DevOps Python Package

**Phase 1 output for**: `002-asgards-azure-devops-package`
**Generated**: 2026-04-15

---

## Class Hierarchy

```
(module-level helper)
└── _build_connection(pat, org_url) → Connection

ProjectClient(pat, org_url)
RepoClient(pat, org_url)
MemberClient(pat, org_url)
PipelineClient(pat, org_url)
ReleaseClient(pat, org_url)
BranchClient(pat, org_url)
```

All six client classes share the same constructor signature. There is no shared base class
to keep implementation minimal (Constitution Principle VIII: no over-engineering).

---

## Shared Constructor Pattern

```python
class XxxClient:
    def __init__(self, pat: str | None = None, org_url: str | None = None):
        """
        Args:
            pat: Azure DevOps Personal Access Token.
                 Falls back to env var AZURE_DEVOPS_PAT if not provided.
            org_url: Organization URL, e.g. "https://dev.azure.com/myorg".
                     Falls back to env var AZURE_DEVOPS_ORG_URL if not provided.
        Raises:
            ValueError: if either credential is missing from both sources.
        """
        connection = _build_connection(pat, org_url)
        self._client = connection.clients.get_xxx_client()
```

---

## Module: `project.py` — `ProjectClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `create(name, description, process_template)` | `name: str`, `description: str = ""`, `process_template: str = "Agile"` | `OperationReference` | `RuntimeError` on API error |
| `get(project_id_or_name)` | `project_id_or_name: str` | `TeamProject` | `RuntimeError` if not found |
| `list()` | — | `list[TeamProjectReference]` | `RuntimeError` |
| `delete(project_id)` | `project_id: str` | `OperationReference` | `RuntimeError` |
| `exists(name)` | `name: str` | `bool` | never raises |

**State transitions**:  
`create()` and `delete()` return `OperationReference` (async operation). Callers poll
`OperationReference.status` to confirm completion if needed.

---

## Module: `repo.py` — `RepoClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `create(project, name)` | `project: str`, `name: str` | `GitRepository` | `RuntimeError` |
| `get(project, repo_id_or_name)` | `project: str`, `repo_id_or_name: str` | `GitRepository` | `RuntimeError` |
| `list(project)` | `project: str` | `list[GitRepository]` | `RuntimeError` |
| `delete(project, repo_id)` | `project: str`, `repo_id: str` | `None` | `RuntimeError` |
| `get_file_content(project, repo_id, file_path, branch)` | all `str` | `str` (decoded UTF-8) | `RuntimeError` |
| `get_file_content_from_source(src_org_url, src_pat, src_project, src_repo, file_path, branch)` | all `str` | `str` | `RuntimeError` |
| `push_file(project, repo_id, file_path, content, branch, commit_message)` | `content: str \| bytes` | `GitPush` | `ValueError` (>5 MB), `RuntimeError` |

**5 MB validation rule** (enforced in `push_file` before any API call):
```
if len(content_bytes) > 5 * 1024 * 1024:
    raise ValueError(f"Content size {len(content_bytes)} exceeds 5 MB limit")
```

**File add vs update logic** (inside `push_file`):
```
try:
    git_client.get_item(repo_id, file_path, project)
    change_type = 2  # edit
except AzureDevOpsServiceError:
    change_type = 1  # add
```

---

## Module: `member.py` — `MemberClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `find_group(project_id, group_display_name)` | `project_id: str`, `group_display_name: str` | `GraphGroup` | `RuntimeError` if not found |
| `add(project_id, group_display_name, user_email)` | all `str` | `None` | `RuntimeError` |
| `remove(project_id, group_display_name, user_email)` | all `str` | `None` | `RuntimeError` |
| `list_members(project_id, group_display_name)` | `project_id: str`, `group_display_name: str` | `list[GraphMember]` | `RuntimeError` |

**Group name constants** (recommended usage):
```python
GROUP_PROJECT_ADMINISTRATORS = "Project Administrators"
GROUP_CONTRIBUTORS = "Contributors"
```

**Lookup chain**:
1. Get project scope descriptor: `graph_client.get_descriptor(project_id)`
2. List groups: `graph_client.list_groups(scope_descriptor=descriptor)`
3. Filter by `group.display_name == group_display_name`

---

## Module: `pipeline.py` — `PipelineClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `create_from_yaml(project, name, repo_id, yaml_path, default_branch)` | all `str` | `BuildDefinition` | `RuntimeError` |
| `list(project)` | `project: str` | `list[BuildDefinitionReference]` | `RuntimeError` |
| `trigger(project, definition_id)` | `project: str`, `definition_id: int` | `Build` | `RuntimeError` |
| `get_run_status(project, build_id)` | `project: str`, `build_id: int` | `str` (one of: `"queued"`, `"running"`, `"succeeded"`, `"failed"`, `"canceled"`) | `RuntimeError` |

**Status normalization** (map SDK enum to plain string):
```
Build.status in {notStarted, postponed} → "queued"
Build.status == inProgress               → "running"
Build.result == succeeded                → "succeeded"
Build.result in {failed, canceled}       → "failed" / "canceled"
```

---

## Module: `release.py` — `ReleaseClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `get_retention_settings(project)` | `project: str` | `dict` with the 5 keys below | `RuntimeError` |
| `set_retention_settings(project, **kwargs)` | `project: str`, + any of the 5 keyword args | `None` | `RuntimeError` |

**Settings dict schema** (both get and set use these keys):
```python
{
    "days_to_keep_deleted_runs": int,   # days before deleted runs are purged
    "days_to_keep": int,                # default retention days
    "maximum_days_to_keep": int,        # maximum allowed retention days
    "maximum_runs_to_keep": int,        # max runs kept per pipeline
    "retain_associated_build": bool,    # retain linked build record
}
```

**`set_retention_settings` partial update**: reads current settings first, merges only
the provided kwargs, then writes back — so callers can update a single field.

---

## Module: `branch.py` — `BranchClient`

| Method | Parameters | Returns | Raises |
|--------|-----------|---------|--------|
| `create(project, repo_id, branch_name, source_ref)` | all `str`; `source_ref` = branch name or commit SHA | `GitRef` | `RuntimeError` |
| `set_policy_work_item(project, repo_id, branch_name)` | all `str` | `PolicyConfiguration` | `RuntimeError` |
| `set_policy_comment_resolution(project, repo_id, branch_name)` | all `str` | `PolicyConfiguration` | `RuntimeError` |
| `set_policy_merge_strategy(project, repo_id, branch_name)` | all `str` | `PolicyConfiguration` | `RuntimeError` |
| `set_all_policies(project, repo_id, branch_name)` | all `str` | `None` | `RuntimeError` |

**`set_all_policies`**: convenience method that calls the three individual policy setters.

**Branch policy GUIDs** (constants in `branch.py`):
```python
POLICY_WORK_ITEM_LINKING     = "40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e"
POLICY_COMMENT_REQUIREMENTS  = "c6a1889d-b943-4856-b76f-9e46bb6b0df3"
POLICY_MERGE_STRATEGY        = "fa4e907d-c16b-452d-8106-7efa0cb84489"
```

---

## Package Public API (`asgards/__init__.py`)

```python
from asgards.src.project import ProjectClient
from asgards.src.repo import RepoClient
from asgards.src.member import MemberClient
from asgards.src.pipeline import PipelineClient
from asgards.src.release import ReleaseClient
from asgards.src.branch import BranchClient

__all__ = [
    "ProjectClient",
    "RepoClient",
    "MemberClient",
    "PipelineClient",
    "ReleaseClient",
    "BranchClient",
]
```
