# Data Model: Azure DevOps CI Pipeline

## Entities

### Pipeline Configuration
- **Location**: `pipelines/main.yml`, `pipelines/templates/*.yml`
- **Fields**: Trigger, Variables, Stages, Jobs, Tasks
- **Validation**: MUST adhere to the Azure Pipelines YAML schema

### SonarQube Project
- **Key**: Unique identifier for the SonarQube project
- **Quality Gate**: Set of criteria defining whether a build passes or fails
- **Properties**: `sonar.projectKey`, `sonar.sources`, `sonar.python.version`

### Test Coverage Report
- **Format**: XML (Cobertura or JUnit)
- **Source**: `pytest-cov` output
- **Artifact**: Published to Azure DevOps for tracking

## State Transitions

1. **Commit Pushed**: Triggers the `main.yml` pipeline.
2. **Install Deps Stage**: Installs Python environment; fails on invalid `requirements.txt`.
3. **Lint & Test Stage**: Runs `ruff` and `pytest`; fails on lint errors or test failures.
4. **SonarQube Analyze**: Sends results to the server; fails on connectivity or server-side issues.
5. **Quality Gate Check**: Waits for asynchronous result; fails if gate criteria not met.
6. **Final Status**: Reports success or failure back to the git commit status.
