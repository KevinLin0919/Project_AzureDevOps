# Research: Asgards — Azure DevOps Python Package

**Phase 0 output for**: `002-asgards-azure-devops-package`
**Generated**: 2026-04-15

---

## 1. SDK Client Mapping per Module

### Decision
Use `azure-devops` Python SDK (`azure.devops.connection.Connection`) as the primary entry
point. Each module receives a pre-built connection and calls `get_client()` to obtain the
appropriate service client.

```python
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

credentials = BasicAuthentication("", pat)
connection = Connection(base_url=org_url, creds=credentials)
```

| Module | Primary SDK Client | SDK Import Path |
|--------|-------------------|-----------------|
| `project.py` | `CoreClient` | `azure.devops.v7_1.core.core_client` |
| `repo.py` | `GitClient` | `azure.devops.v7_1.git.git_client` |
| `member.py` | `GraphClient` | `azure.devops.v7_1.graph.graph_client` |
| `pipeline.py` | `BuildClient` | `azure.devops.v7_1.build.build_client` |
| `release.py` | `BuildClient` | `azure.devops.v7_1.build.build_client` |
| `branch.py` | `GitClient` + `PolicyClient` | `git_client` + `azure.devops.v7_1.policy.policy_client` |

**Rationale**: The `azure-devops` SDK wraps all primary REST endpoints and handles auth
token encoding automatically via `msrest`. Using `requests` directly would require manual
Base64 encoding of the PAT and URL construction.

**Alternatives considered**: `requests` only — rejected because it requires significant
boilerplate for auth, error handling, and response parsing that the SDK handles for free.

---

## 2. Key SDK Method Mapping

### project.py (CoreClient)

| Operation | SDK Method |
|-----------|-----------|
| Create project | `core_client.queue_create_project(project_parameters)` → returns `OperationReference` |
| Get project | `core_client.get_project(project_id_or_name)` |
| List projects | `core_client.get_projects()` |
| Delete project | `core_client.queue_delete_project(project_id)` |
| Exists check | Call `get_project()`, return `False` if `AzureDevOpsServiceError` with 404 status |

### repo.py (GitClient)

| Operation | SDK Method |
|-----------|-----------|
| Create repo | `git_client.create_repository(git_repository_to_create, project)` |
| Get repo | `git_client.get_repository(repository_id, project)` |
| List repos | `git_client.get_repositories(project)` |
| Delete repo | `git_client.delete_repository(repository_id, project)` |
| Get file content | `git_client.get_item_content(repository_id, path, project, version_descriptor)` |
| Push commit (create/update file) | `git_client.create_push(push, repository_id, project)` |

**Cross-source file retrieval**: Instantiate a separate `Connection` to the source
organization (with its own PAT/org_url) and call `git_client.get_item_content()` on that
connection. The function signature accepts `src_org_url`, `src_pat`, `src_project`,
`src_repo`, and `file_path`.

**5 MB enforcement**:
```python
FILE_SIZE_LIMIT_BYTES = 5 * 1024 * 1024
if len(content.encode()) > FILE_SIZE_LIMIT_BYTES:
    raise ValueError(f"File exceeds 5 MB limit ({len(content)} bytes)")
```

**Push commit pattern**:
```python
from azure.devops.v7_1.git.models import GitPush, GitCommit, GitChange, ItemContent

push = GitPush(
    commits=[GitCommit(
        comment="chore: push file via asgards",
        changes=[GitChange(
            change_type=1,  # 1=add, 2=edit
            item={"path": file_path},
            new_content=ItemContent(content=content, content_type=0)  # 0=rawtext
        )]
    )],
    ref_updates=[{"name": f"refs/heads/{branch}", "oldObjectId": last_commit_sha}]
)
git_client.create_push(push, repository_id=repo_id, project=project)
```
To distinguish add vs edit: first call `get_item()` — if it raises, the file doesn't exist
(use `change_type=1`); if it succeeds, use `change_type=2`.

### member.py (GraphClient)

| Operation | SDK Method |
|-----------|-----------|
| Get project scope descriptor | `graph_client.get_descriptor(storage_key=project_id)` |
| List groups in project | `graph_client.list_groups(scope_descriptor=project_descriptor)` |
| Find group by name | Filter `list_groups()` result by `group.principal_name` or `group.display_name` |
| Add member | `graph_client.add_member_to_group(subject_descriptor, container_descriptor)` |
| Remove member | `graph_client.remove_member_from_group(container_descriptor, member_descriptor)` |
| List members | `graph_client.list_memberships(subject_descriptor, direction="down")` |

**Group name patterns**:
- `Project Administrators` → display name `"Project Administrators"` or principal name `"[ProjectName]\Project Administrators"`
- `Contributors` → display name `"Contributors"`

### pipeline.py (BuildClient)

| Operation | SDK Method |
|-----------|-----------|
| Create pipeline from YAML | `build_client.create_definition(definition, project)` |
| List pipelines | `build_client.get_definitions(project)` |
| Trigger run | `build_client.queue_build(build, project)` |
| Get run status | `build_client.get_build(build_id, project)` → `.status` field |

**YAML-to-definition object**:
```python
from azure.devops.v7_1.build.models import BuildDefinition, BuildRepository

definition = BuildDefinition(
    name=pipeline_name,
    queue={"pool": {"name": "Azure Pipelines"}},
    repository=BuildRepository(
        id=repo_id,
        type="TfsGit",
        default_branch="refs/heads/main"
    ),
    process={"yamlFilename": yaml_path, "type": 2}  # type 2 = YAML
)
```

### release.py (BuildClient — build settings)

| Field (spec) | SDK Path |
|---|---|
| `days_to_keep_deleted_runs` | `BuildSettings.days_to_keep_deleted_builds_before_delete` |
| `days_to_keep` | `BuildSettings.default_retention_policy.days_to_keep` |
| `maximum_days_to_keep` | `BuildSettings.maximum_retention_policy.days_to_keep` |
| `maximum_runs_to_keep` | `BuildSettings.maximum_retention_policy.artifacts_to_keep` |
| `retain_associated_build` | `BuildSettings.default_retention_policy.keep_forever` (bool) |

```python
settings = build_client.get_build_settings(project)
settings.days_to_keep_deleted_builds_before_delete = days_to_keep_deleted_runs
settings.default_retention_policy.days_to_keep = days_to_keep
# ... etc.
build_client.update_build_settings(settings, project)
```

**Note**: `retain_associated_build` maps to `keep_forever` on the default retention policy
object. Verify the exact field name at implementation time by inspecting
`BuildSettings.__dict__` against the live API response.

### branch.py (GitClient + PolicyClient)

**Create branch**:
```python
from azure.devops.v7_1.git.models import GitRefUpdate

git_client.update_refs(
    ref_updates=[GitRefUpdate(
        name=f"refs/heads/{branch_name}",
        old_object_id="0000000000000000000000000000000000000000",
        new_object_id=source_sha
    )],
    repository_id=repo_id,
    project=project
)
```
If `source_ref` is a branch name (not a SHA), resolve it first:
```python
git_client.get_refs(repo_id, project, filter=f"heads/{source_branch}")[0].object_id
```

**Branch policy type IDs** (well-known Azure DevOps GUIDs):

| Policy | Type ID GUID | Verify via |
|--------|-------------|-----------|
| Work item linking | `40e92b44-2fe1-4dd6-b3d8-74a9c21d0c6e` | `policy_client.get_policy_types(project)` |
| Comment requirements | `c6a1889d-b943-4856-b76f-9e46bb6b0df3` | `policy_client.get_policy_types(project)` |
| Merge strategy | `fa4e907d-c16b-452d-8106-7efa0cb84489` | `policy_client.get_policy_types(project)` |

> **Implementation note**: Always verify GUIDs at runtime by calling
> `policy_client.get_policy_types(project)` and matching by `display_name`. The GUIDs
> above are from documented sources but can differ between Azure DevOps Services versions.

**Merge strategy config (Basic merge / no fast-forward)**:
```python
{
    "allowSquash": False,
    "allowNoFastForward": True,   # Basic merge = merge commit, no fast-forward
    "allowRebase": False,
    "allowRebaseMerge": False
}
```

**Policy create payload**:
```python
from azure.devops.v7_1.policy.models import PolicyConfiguration, PolicyType

config = PolicyConfiguration(
    type=PolicyType(id=type_guid),
    is_enabled=True,
    is_blocking=True,
    settings={
        "scope": [{"refName": f"refs/heads/{branch_name}", "matchKind": "Exact",
                   "repositoryId": repo_id}],
        # ... policy-specific settings
    }
)
policy_client.create_policy_configuration(config, project)
```

---

## 3. Authentication Pattern (shared across all modules)

```python
import os
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def _build_connection(pat: str | None, org_url: str | None) -> Connection:
    pat = pat or os.environ.get("AZURE_DEVOPS_PAT")
    org_url = org_url or os.environ.get("AZURE_DEVOPS_ORG_URL")
    if not pat:
        raise ValueError("PAT required: pass 'pat' or set AZURE_DEVOPS_PAT env var")
    if not org_url:
        raise ValueError("Org URL required: pass 'org_url' or set AZURE_DEVOPS_ORG_URL env var")
    return Connection(base_url=org_url, creds=BasicAuthentication("", pat))
```

**Decision**: Implement `_build_connection()` as a module-level helper in each client file
(or in a shared `_auth.py`). Each `Client.__init__` calls it.

**Rationale**: Keeps auth logic DRY. A single `_auth.py` shared module avoids duplication
across 6 client files.

**Alternatives considered**: Singleton connection pool — rejected because each client
instantiation is lightweight and lifetime management would add unnecessary complexity.

---

## 4. Error Handling Strategy

- Catch `azure.devops.exceptions.AzureDevOpsServiceError` for SDK calls
- Re-raise as `RuntimeError(f"Azure DevOps API error: {e.message}")` with context
- `exists()` methods catch 404 specifically and return `False` instead of raising
- All other errors propagate — callers decide how to handle them

---

## 5. Test Strategy

Use `unittest.mock.MagicMock` to mock SDK client objects. Pattern:

```python
from unittest.mock import MagicMock, patch

def test_create_project():
    with patch("asgards.src.project.Connection") as mock_conn:
        mock_core = MagicMock()
        mock_conn.return_value.clients.get_core_client.return_value = mock_core
        client = ProjectClient(pat="fake", org_url="https://dev.azure.com/test")
        client.create("MyProject")
        mock_core.queue_create_project.assert_called_once()
```

No real Azure DevOps credentials needed in tests — all network calls are mocked.
