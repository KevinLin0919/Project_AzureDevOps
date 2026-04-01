# Contract: Azure DevOps Pipeline Configuration

## Schema: YAML (Azure Pipelines)

### Properties

| Key | Description | Requirement |
|-----|-------------|-------------|
| `trigger` | Defines branch/tag conditions for auto-triggering. | MUST include `main` and feature branches. |
| `pool` | Specifies the agent pool (e.g., `vmImage: 'ubuntu-latest'`). | MUST use Linux-based agents for Python. |
| `variables` | List of pipeline variables. | MUST include `sonarConnectionName`. |
| `stages` | Logical grouping of jobs. | MUST have `Build`, `Test`, `Analyze` stages. |

### SonarQube Parameters

- **Task**: `SonarQubePrepare`
- **Scanner Mode**: `CLI`
- **Config Mode**: `Manual`
- **Project Key**: Unique repo ID
- **Sources**: `asgards/`

### Validation Logic

The pipeline configuration MUST be valid per the `az pipelines validate` command.
Any deviation from the standard `pipelines/` or `asgards/` pathing MUST be documented in `Complexity Tracking`.
