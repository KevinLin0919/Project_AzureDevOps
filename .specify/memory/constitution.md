<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- List of modified principles:
    - I.  Scalable and Maintainable Pipelines (unchanged)
    - II. Automated CI/CD Lifecycle (unchanged)
    - III. Quality Gates via SonarQube (unchanged)
    - IV. Standardized Project Structure (expanded: asgards package layout added)
    - V.  Python Reliability and Testability (unchanged)
    - VI. Python Package Structure & Installability (NEW)
    - VII. Module-to-Test Correspondence (NEW)
    - VIII. Azure DevOps API Layer Design (NEW)
    - IX. Authentication Contract (NEW)
- Added sections: Principles VI–IX covering Python package development
- Removed sections: None
- Templates requiring updates:
    - ✅ .specify/memory/constitution.md (this file)
    - ⚠ .specify/templates/plan-template.md (Constitution Check section references new principles VI–IX)
    - ⚠ .specify/templates/tasks-template.md (Path Conventions should note asgards/src/ layout)
- Follow-up TODOs: None
-->

# Azure DevOps Project Constitution

## Core Principles

### I. Scalable and Maintainable Pipelines

All pipeline configurations MUST be written in YAML and stored in the `pipelines/` directory.
Logic SHOULD be modularized using templates to ensure reproducibility and ease of maintenance.
Inline scripts MUST be avoided where Azure DevOps tasks or YAML templates are available.

### II. Automated CI/CD Lifecycle

Every code change MUST trigger an automated pipeline that includes linting, testing, and
security scanning. Manual steps in the critical path MUST be eliminated to ensure rapid and
reliable delivery. Automation is the default state.

### III. Quality Gates via SonarQube

Static code analysis using SonarQube is mandatory for all Python source code in the
`asgards/` directory. Pipelines MUST fail if SonarQube quality gates are not met.
Quality is a blocking requirement, not an afterthought.

### IV. Standardized Project Structure

The repository MUST follow this defined layout. Deviations require explicit justification
and a constitutional amendment.

```
Project_AzureDevops/
├── pipelines/              ← Azure DevOps pipeline YAML and templates
│   ├── main.yml
│   └── templates/
├── asgards/                ← Python package root (pip-installable)
│   ├── setup.py
│   ├── __init__.py
│   ├── src/                ← Module source files
│   │   ├── __init__.py
│   │   ├── project.py
│   │   ├── repo.py
│   │   ├── member.py
│   │   ├── pipeline.py
│   │   ├── release.py
│   │   └── branch.py
│   └── tests/              ← One test file per source module
│       ├── test_project.py
│       ├── test_repo.py
│       ├── test_member.py
│       ├── test_pipeline.py
│       ├── test_release.py
│       └── test_branch.py
├── specs/                  ← Spec-kit specification documents
│   ├── 001-azure-devops-ci-pipeline/
│   └── 002-asgards-azure-devops-package/
└── sonar-project.properties
```

### V. Python Reliability and Testability

Python code MUST be accompanied by comprehensive unit tests using `pytest`.
Test coverage reports MUST be generated and uploaded as pipeline artifacts.
Reliability and reproducible test results are non-negotiable.

### VI. Python Package Structure & Installability

The `asgards` package MUST be structured so it can be installed directly from the Git
repository without publishing to PyPI:

```bash
pip install git+https://github.com/<org>/<repo>.git
```

This requires a valid `asgards/setup.py` (or `pyproject.toml`) that declares the package
name, version, and `install_requires`. All public classes and functions intended for external
use MUST be re-exported through `asgards/__init__.py` so callers can write
`from asgards import ProjectClient` rather than importing from internal submodules.

### VII. Module-to-Test Correspondence

Every source module in `asgards/src/` MUST have a corresponding test file in
`asgards/tests/` with the naming convention `test_<module>.py`.
A module MUST NOT be merged if its test file is absent or contains only placeholder
comments. CI will enforce this by measuring per-file coverage and failing below threshold.

### VIII. Azure DevOps API Layer Design

When wrapping Azure DevOps REST endpoints in `asgards/src/`:

1. **SDK first**: Use the official `azure-devops` Python SDK
   (`azure.devops.connection.Connection`) whenever the target endpoint is covered.
2. **Requests fallback**: Only use the `requests` library for endpoints not covered by the
   SDK (e.g., certain policy or retention APIs). Raw HTTP calls MUST include error-status
   checking and raise a descriptive `RuntimeError` or a custom exception on failure.
3. **No silent failures**: Functions MUST NOT return `None` to signal an error.
   Use exceptions so callers can handle failures explicitly.
4. **5 MB file limit**: Any function that pushes file content to a repository MUST
   validate the payload size before making an API call and raise `ValueError` if it
   exceeds 5 MB (5 × 1024 × 1024 bytes).

### IX. Authentication Contract

All `asgards/src/` client classes MUST accept credentials through two mechanisms,
with the following priority order:

1. **Constructor arguments** (highest priority):
   `pat` (Personal Access Token) and `org_url` (organization URL).
2. **Environment variables** (fallback):
   `AZURE_DEVOPS_PAT` and `AZURE_DEVOPS_ORG_URL`.

If neither source provides a value at the time the client is instantiated, the constructor
MUST raise `ValueError` with a clear message indicating which credential is missing.
Hard-coded tokens in source code are strictly prohibited and MUST be caught by code review.

## Technology Stack & Constraints

- **CI/CD Platform**: Azure DevOps Services / Server
- **Language**: Python 3.11
- **Azure DevOps SDK**: `azure-devops` (primary), `msrest` (auth helpers)
- **HTTP Fallback**: `requests` (only when SDK does not cover the endpoint)
- **Quality Tools**: SonarQube (integrated via Azure DevOps tasks)
- **Testing Framework**: `pytest` with `pytest-cov`
- **Linting**: `ruff`

## Development Workflow

- **Methodology**: Vibe coding + Specification-Driven Development (SDD) via spec-kit.
  All features MUST follow the flow: spec → clarify → plan → tasks → implement.
- **Branching**: Gitflow or Trunk-based development SHOULD be used.
- **Protection**: Branch protection rules MUST be enforced on the primary branch.
- **Pull Requests**: All PRs MUST pass the full CI suite (lint → tests → SonarQube)
  before they are eligible for merge.
- **Review**: Pipeline changes MUST be reviewed for security, efficiency, and modularity.

## Governance

- The Constitution is the supreme authority for project standards.
- Amendments require a version bump (SemVer) and a corresponding update to the Sync
  Impact Report at the top of this file.
- Versioning:
    - MAJOR: Structural changes to the repo or removal of core quality gates.
    - MINOR: New principles or sections added, or materially expanded guidance.
    - PATCH: Clarifications, wording fixes, formatting.

**Version**: 1.1.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-15
