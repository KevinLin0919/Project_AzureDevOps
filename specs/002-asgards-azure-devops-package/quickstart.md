# Quickstart: Asgards Package

## Prerequisites

- Python 3.11+
- An Azure DevOps organization with a Personal Access Token (PAT)
- PAT scopes required:
  - **Project and Team** (Read & Write)
  - **Code** (Read & Write)
  - **Build** (Read & Execute)
  - **Graph** (Read & Manage)
  - **Release** (Read, Write & Execute) — for retention policy

---

## Installation

```bash
# From GitHub (no PyPI publishing needed)
pip install git+https://github.com/<your-org>/<your-repo>.git#subdirectory=asgards

# Or in development mode from the repo root
cd asgards
pip install -e .
```

---

## Authentication Setup

Set credentials as environment variables (or pass them directly to each client):

```bash
export AZURE_DEVOPS_PAT="your-personal-access-token"
export AZURE_DEVOPS_ORG_URL="https://dev.azure.com/your-org"
```

Constructor arguments take priority over environment variables:

```python
from asgards import ProjectClient

# Uses env vars
client = ProjectClient()

# Explicit credentials override env vars
client = ProjectClient(pat="my-pat", org_url="https://dev.azure.com/myorg")
```

---

## Basic Usage

### Project Management

```python
from asgards import ProjectClient

projects = ProjectClient()

# Check existence before creating
if not projects.exists("MyProject"):
    op = projects.create("MyProject", description="Created via asgards")
    print(f"Create operation queued: {op.id}")

# List all projects
for p in projects.list():
    print(p.name)
```

### Repository Operations

```python
from asgards import RepoClient

repos = RepoClient()

# Create a repo
repo = repos.create(project="MyProject", name="my-repo")

# Push a file (raises ValueError if content > 5 MB)
repos.push_file(
    project="MyProject",
    repo_id=repo.id,
    file_path="/README.md",
    content="# Hello from asgards",
    branch="main",
    commit_message="docs: add README"
)

# Retrieve a file from a different org/repo
content = repos.get_file_content_from_source(
    src_org_url="https://dev.azure.com/other-org",
    src_pat="other-pat",
    src_project="SourceProject",
    src_repo="source-repo",
    file_path="/config/settings.yml",
    branch="main"
)
```

### Member Management

```python
from asgards import MemberClient

members = MemberClient()

# Add a user to Project Administrators
members.add(
    project_id="<project-guid>",
    group_display_name="Project Administrators",
    user_email="alice@example.com"
)

# List contributors
for m in members.list_members("<project-guid>", "Contributors"):
    print(m.display_name, m.principal_name)
```

### Pipeline from YAML

```python
from asgards import PipelineClient

pipelines = PipelineClient()

# Create a pipeline pointing to an existing YAML file in a repo
defn = pipelines.create_from_yaml(
    project="MyProject",
    name="CI Pipeline",
    repo_id="<repo-guid>",
    yaml_path="/pipelines/main.yml",
    default_branch="main"
)

# Trigger a run
build = pipelines.trigger(project="MyProject", definition_id=defn.id)
print(f"Build queued: #{build.id} — {pipelines.get_run_status('MyProject', build.id)}")
```

### Retention Policy

```python
from asgards import ReleaseClient

releases = ReleaseClient()

releases.set_retention_settings(
    project="MyProject",
    days_to_keep=30,
    maximum_days_to_keep=365,
    maximum_runs_to_keep=10,
    days_to_keep_deleted_runs=7,
    retain_associated_build=True
)
```

### Branch + Policies

```python
from asgards import BranchClient

branches = BranchClient()

# Create a branch from main
branches.create(
    project="MyProject",
    repo_id="<repo-guid>",
    branch_name="feature/my-feature",
    source_ref="main"
)

# Enforce all three policies in one call
branches.set_all_policies(
    project="MyProject",
    repo_id="<repo-guid>",
    branch_name="main"
)
```

---

## Running Tests

```bash
cd asgards
pytest tests/ --cov=src --cov-report=term-missing
```

All tests use mocks — no real Azure DevOps credentials needed to run them.
