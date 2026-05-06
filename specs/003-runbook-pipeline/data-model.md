# Data Model: Runbook Pipeline

**Branch**: `003-runbook-pipeline` | **Phase**: 1

## Pipeline Parameter Schema

### 共用參數（所有 runbook）

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `runbook` | string (enum) | Yes | — | 選擇執行的 runbook：`create_project` / `modify_member` |
| `project_name` | string | Yes | — | 目標或新建的 Azure DevOps 專案名稱 |

### create_project 專用參數

| Parameter | Type | Required | Default | Maps to CLI arg |
|-----------|------|----------|---------|-----------------|
| `pipeline_name` | string | No | `"CI Pipeline"` | `--pipeline-name` |
| `managers` | string | No | `""` | `--managers`（空白分隔多筆 email） |
| `members` | string | No | `""` | `--members`（空白分隔多筆 email） |

### modify_member 專用參數

| Parameter | Type | Required | Default | Maps to CLI arg |
|-----------|------|----------|---------|-----------------|
| `add_manager` | string | No | `""` | `--add-manager`（空白分隔多筆 email） |
| `remove_manager` | string | No | `""` | `--remove-manager`（空白分隔多筆 email） |
| `add_member` | string | No | `""` | `--add-member`（空白分隔多筆 email） |
| `remove_member` | string | No | `""` | `--remove-member`（空白分隔多筆 email） |

## Secret Variables（Pipeline Variables UI 設定）

| Variable | Secret | Source | Used by |
|----------|--------|--------|---------|
| `AZURE_DEVOPS_PAT` | Yes | Pipeline Variables UI | 兩個 runbook 的 `_auth.py` |
| `AZURE_DEVOPS_ORG_URL` | No | Pipeline Variables UI | 兩個 runbook 的 `_auth.py` |

## 執行流程

```
使用者點 Run Pipeline
    ↓
Azure DevOps 顯示 Parameters UI（由 YAML parameters 區段定義）
    ↓
使用者選擇 runbook 並填入對應欄位
    ↓
Agent checkout repo
    ↓
Step 1: UsePythonVersion@0 (3.11)
    ↓
Step 2: pip install -r asgards/requirements.txt && pip install -e asgards/
    ↓
${{ if eq(parameters.runbook, 'create_project') }}
    └─ Step 3a: python runbooks/create_project.py [args]
       env: AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG_URL
${{ if eq(parameters.runbook, 'modify_member') }}
    └─ Step 3b: python runbooks/modify_member.py [args]
       env: AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG_URL
    ↓
Pipeline 結束（exit code 由 Python script 決定）
```

## Email 參數展開規則

空字串 `""` → 不傳入對應 flag（shell conditional）
非空字串 `"a@b.com c@d.com"` → 空白分隔展開 → argparse `nargs="*"` 接收多個值

```bash
# shell conditional pattern（適用所有 email 參數）
[ -n "$MANAGERS" ] && MANAGERS_FLAG="--managers $MANAGERS" || MANAGERS_FLAG=""
python runbooks/create_project.py --project "$PROJECT_NAME" $MANAGERS_FLAG ...
```
