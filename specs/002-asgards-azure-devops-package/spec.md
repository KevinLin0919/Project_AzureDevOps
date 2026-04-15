# Spec: Asgards — Azure DevOps Python Package (Weeks 4-5)

## Overview

Build the `asgards` Python package that wraps the Azure DevOps REST API, providing
programmatic access to Azure DevOps resources via clean, testable Python function calls.
The package must be installable directly from GitHub via `pip install git+<repo_url>`.

## Problem Statement

Direct use of Azure DevOps REST API requires repetitive boilerplate (authentication,
HTTP handling, error parsing). The `asgards` package abstracts this into a clean,
module-based interface so downstream tools (AI agent, CI pipeline) can interact with
Azure DevOps without dealing with raw HTTP.

## Package Structure

Follows the Python package convention from the reference material:

```
asgards/
├── setup.py                  ← enables pip install git+...
├── __init__.py               ← exposes top-level public API
├── src/
│   ├── __init__.py
│   ├── project.py
│   ├── repo.py
│   ├── member.py
│   ├── pipeline.py
│   ├── release.py
│   └── branch.py
└── tests/
    ├── test_project.py
    ├── test_repo.py
    ├── test_member.py
    ├── test_pipeline.py
    ├── test_release.py
    └── test_branch.py
```

## Functional Requirements

### 1. Project Management (`project.py`)

- Create a new Azure DevOps project
- Get project info by name or ID
- List all projects in an organization
- Delete a project
- Check whether a project exists (return bool, do not raise on 404)

### 2. Repository Operations (`repo.py`)

- Create, get, list, delete Git repositories within a project
- **Cross-source file retrieval**: given a source organization + project + repo + file path,
  retrieve the raw file content (bytes or string). The source can be a different project or
  repo than the caller's own.
- **File push as commit**: push file content (string or bytes) to a specified repo path,
  creating a new commit on a target branch. If the file already exists, update it; if not,
  create it.
- Enforce 5 MB file size limit on upload — raise `ValueError` before making the API call
  if the content exceeds 5 MB.

### 3. Team & Member Management (`member.py`)

- **Find group descriptor**: look up the descriptor ID for the built-in groups
  `Project Administrators` and `Contributors` (or any named group) within a project.
- Add a user (by email / principal name) to a specified group
- Remove a user from a specified group
- List current members of a group

### 4. Pipeline Configuration (`pipeline.py`)

- Given a YAML file path that exists inside a repo, create an Azure DevOps build pipeline
  definition pointing to that YAML file
- List all pipelines in a project
- Trigger a pipeline run (queue a build)
- Get the status of a pipeline run (queued / running / succeeded / failed)

### 5. Release Retention Policy (`release.py`)

Configure the four retention settings available from the Azure DevOps UI under
**Project Settings → Pipelines → Settings → Retention policy**:

- `days_to_keep_deleted_runs` — number of days to retain runs after they are deleted from
  the UI ("從 UI 上刪除的保留天數")
- `days_to_keep` — default number of days to retain runs ("預設保留天數")
- `maximum_days_to_keep` — maximum days allowed for retention ("最高保留天數")
- `maximum_runs_to_keep` — maximum number of runs to keep per pipeline ("保留代數")
- `retain_associated_build` — boolean, whether to retain the associated build record when
  a run is retained ("設定預設是否保留關聯的 Build 記錄")

### 6. Branch Management (`branch.py`)

- Create a new branch from a source ref (branch name or full commit SHA)
- Set the following branch policies on a target branch:
  - **Work Item binding**: PRs targeting this branch must be linked to at least one work item
  - **Comment resolution**: all PR comments must be resolved before merge
    (`Check for comment resolution`)
  - **Merge strategy**: enforce "Basic merge (no fast-forward)" — no squash, no rebase,
    commits are retained as-is with a merge commit

## Non-Functional Requirements

- Authentication via Azure DevOps Personal Access Token (PAT)
  - Passed via constructor argument **or** env var `AZURE_DEVOPS_PAT` (constructor takes priority)
- Organization URL passed via constructor argument **or** env var `AZURE_DEVOPS_ORG_URL`
- Use the official `azure-devops` Python SDK where endpoints are available; fall back to
  direct `requests` calls only when the SDK does not cover the endpoint
- All modules must pass `ruff` linting (enforced by CI)
- Test coverage tracked via `pytest-cov` and uploaded to SonarCloud
- API errors must raise descriptive Python exceptions — do not silently return `None`
- The package must be installable via `pip install git+<repo_url>` (requires `setup.py`)

## Out of Scope (Weeks 4-5)

- AI-assisted PR / Work Item commenting (planned for Weeks 7-8)
- Web UI or dashboard
- OAuth / AAD authentication (PAT only for now)

## Success Criteria

- All 6 modules implemented with corresponding unit tests
- CI pipeline passes: lint (ruff) → tests (pytest) → SonarCloud quality gate
- Package installable via `pip install git+...`
- Each module importable via `from asgards.src.<module> import <Class>`
- `specs/002-asgards-azure-devops-package/quickstart.md` documents PAT setup and basic usage
