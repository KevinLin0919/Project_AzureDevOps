# Quickstart: Azure DevOps CI Pipeline

## Prerequisites
- Azure DevOps Project
- SonarQube Server instance (accessible from Azure)
- Azure DevOps Service Connection named `sonarqube-server`

## Setup Steps

1. **Repository Layout**: Ensure `pipelines/` and `asgards/` directories exist in the root.
2. **Install Dependencies**:
   - `asgards/requirements.txt` should contain `pytest`, `pytest-cov`, and `ruff`.
3. **Configure Service Connection**:
   - Go to Azure DevOps -> Project Settings -> Service Connections.
   - Create a new "SonarQube" service connection.
4. **Create Pipeline**:
   - Create a new Azure Pipeline pointing to `pipelines/main.yml`.
5. **Execute**:
   - Push a commit to trigger the first run.

## Troubleshooting
- **Linter Failures**: Run `ruff check asgards/` locally.
- **Test Failures**: Run `pytest asgards/tests/` locally.
- **SonarQube Connection Errors**: Verify the Service Connection and network access.
