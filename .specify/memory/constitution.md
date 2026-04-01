<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- List of modified principles: Initial creation
- Added sections: Core Principles, Technology Stack & Constraints, Development Workflow, Governance
- Removed sections: None
- Templates requiring updates: 
    - ✅ .specify/templates/plan-template.md (Updated Project Structure defaults)
    - ⚠ .specify/templates/spec-template.md (Pending specific Azure DevOps requirements)
    - ⚠ .specify/templates/tasks-template.md (Pending specific Azure DevOps task types)
- Follow-up TODOs: None
-->

# Azure DevOps CI Pipeline Project Constitution

## Core Principles

### I. Scalable and Maintainable Pipelines
All pipeline configurations MUST be written in YAML and stored in the `pipelines/` directory. Logic SHOULD be modularized using templates to ensure reproducibility and ease of maintenance. Avoid inline scripts where tasks or templates are available.

### II. Automated CI/CD Lifecycle
Every code change MUST trigger an automated pipeline that includes linting, testing, and security scanning. Manual steps in the critical path SHOULD be eliminated to ensure rapid and reliable delivery. Automation is the default state.

### III. Quality Gates via SonarQube
Static code analysis using SonarQube is mandatory for all Python source code in the `asgards/` directory. Pipelines MUST fail if SonarQube quality gates are not met. Quality is a blocking requirement, not an afterthought.

### IV. Standardized Project Structure
The repository MUST follow the defined structure: `pipelines/` for Azure Pipeline YAML files and `asgards/` for Python source code. Deviations require explicit justification and constitutional amendment to ensure cross-project predictability.

### V. Python Reliability and Testability
Python code MUST be accompanied by comprehensive unit tests using `pytest`. Test coverage reports MUST be generated and uploaded as pipeline artifacts. Reliability and reproducible test results are non-negotiable.

## Technology Stack & Constraints

- **CI/CD Platform**: Azure DevOps Services / Server.
- **Language**: Python 3.x (latest stable preferred).
- **Quality Tools**: SonarQube (Integration via Azure DevOps tasks).
- **Testing Framework**: `pytest` with `pytest-cov`.
- **Linting**: `ruff` or `flake8` for style enforcement.

## Development Workflow

- **Branching**: A Gitflow or Trunk-based development model SHOULD be used.
- **Protection**: Branch protection rules MUST be enforced on the primary branch(es).
- **Pull Requests**: All PRs MUST pass the full CI suite (linting, tests, SonarQube) before they are eligible for merge.
- **Review**: Pipeline changes MUST be reviewed for security, efficiency, and adherence to modularity principles.

## Governance

- The Constitution is the supreme authority for project standards.
- Amendments require a version bump (SemVer) and a corresponding update to the Sync Impact Report.
- Versioning:
    - MAJOR: Structural changes to the repo or removal of core quality gates.
    - MINOR: New tools or updated principle guidance.
    - PATCH: Clarifications and formatting.

**Version**: 1.0.0 | **Ratified**: 2026-04-02 | **Last Amended**: 2026-04-02
