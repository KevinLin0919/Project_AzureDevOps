# Project_AzureDevops Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-15

## Active Technologies
- Python 3.11 + `azure-devops>=7.1.0b4`, `msrest>=0.7.1`, `requests>=2.31` (002-asgards-azure-devops-package)
- N/A — pure API wrapper, no local persistence (002-asgards-azure-devops-package)

- Python 3.11 + `pytest`, `pytest-cov`, `ruff`, `azure-devops`, `msrest`

## Project Structure

```text
asgards/
  src/
    main.py       # weeks 1-3 placeholder (sum_even_numbers)
    project.py    # Project CRUD + existence check
    repo.py       # Repo CRUD + file content (5 MB limit)
    member.py     # Team/group member management
    pipeline.py   # YAML-to-build, trigger, status
    release.py    # Retention policy configuration
    branch.py     # Branch creation + policy enforcement
  tests/
    test_main.py
    test_project.py
    test_repo.py
    test_member.py
    test_pipeline.py
    test_release.py
    test_branch.py
pipelines/
  main.yml                    # CI: lint → test → SonarCloud
  templates/
    install-deps.yml
    run-tests.yml
    performance-benchmarking.yml
    sonarqube-analysis.yml
specs/
  001-azure-devops-ci-pipeline/   # weeks 1-3 spec
  002-asgards-azure-devops-package/  # weeks 4-5 spec
```

## Commands

```bash
# Lint
ruff check asgards/

# Test with coverage
pytest asgards/tests/ --cov=asgards/src --cov-report=term-missing
```

## Environment Variables

- `AZURE_DEVOPS_PAT` — Personal Access Token for Azure DevOps API auth
- `AZURE_DEVOPS_ORG_URL` — Organization URL (e.g. `https://dev.azure.com/myorg`)

## Code Style

Python 3.11: Follow standard conventions. All modules in `asgards/src/` must pass `ruff` linting.

## Recent Changes
- 002-asgards-azure-devops-package: Added Python 3.11 + `azure-devops>=7.1.0b4`, `msrest>=0.7.1`, `requests>=2.31`

- 001-azure-devops-ci-pipeline: CI pipeline with lint, test, SonarCloud
- 002-asgards-azure-devops-package: Asgards Azure DevOps Python package (weeks 4-5)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
