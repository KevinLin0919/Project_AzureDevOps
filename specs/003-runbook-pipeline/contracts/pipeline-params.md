# Contract: runbook-pipeline.yml Parameters

**Type**: Azure DevOps Pipeline Parameter Contract
**File**: `pipelines/runbook-pipeline.yml`

## YAML Parameters Block

```yaml
parameters:
- name: runbook
  displayName: 選擇 Runbook
  type: string
  values:
    - create_project
    - modify_member

- name: project_name
  displayName: 專案名稱
  type: string
  default: ''

- name: pipeline_name
  displayName: Pipeline 名稱 (create_project 用)
  type: string
  default: 'CI Pipeline'

- name: managers
  displayName: Project Manager emails (空白分隔，create_project 用)
  type: string
  default: ''

- name: members
  displayName: Project Member emails (空白分隔，create_project 用)
  type: string
  default: ''

- name: add_manager
  displayName: 新增 Project Manager emails (modify_member 用)
  type: string
  default: ''

- name: remove_manager
  displayName: 移除 Project Manager emails (modify_member 用)
  type: string
  default: ''

- name: add_member
  displayName: 新增 Project Member emails (modify_member 用)
  type: string
  default: ''

- name: remove_member
  displayName: 移除 Project Member emails (modify_member 用)
  type: string
  default: ''
```

## CLI Mapping Contract

### create_project

```
python runbooks/create_project.py \
  --project "$PROJECT_NAME" \
  --pipeline-name "$PIPELINE_NAME" \
  $MANAGERS_FLAG \
  $MEMBERS_FLAG
```

Shell 前置處理：
```bash
[ -n "$MANAGERS" ] && MANAGERS_FLAG="--managers $MANAGERS" || MANAGERS_FLAG=""
[ -n "$MEMBERS" ]  && MEMBERS_FLAG="--members $MEMBERS"    || MEMBERS_FLAG=""
```

### modify_member

```
python runbooks/modify_member.py \
  --project "$PROJECT_NAME" \
  $ADD_MANAGER_FLAG \
  $REMOVE_MANAGER_FLAG \
  $ADD_MEMBER_FLAG \
  $REMOVE_MEMBER_FLAG
```

Shell 前置處理：
```bash
[ -n "$ADD_MANAGER" ]    && ADD_MANAGER_FLAG="--add-manager $ADD_MANAGER"       || ADD_MANAGER_FLAG=""
[ -n "$REMOVE_MANAGER" ] && REMOVE_MANAGER_FLAG="--remove-manager $REMOVE_MANAGER" || REMOVE_MANAGER_FLAG=""
[ -n "$ADD_MEMBER" ]     && ADD_MEMBER_FLAG="--add-member $ADD_MEMBER"          || ADD_MEMBER_FLAG=""
[ -n "$REMOVE_MEMBER" ]  && REMOVE_MEMBER_FLAG="--remove-member $REMOVE_MEMBER"  || REMOVE_MEMBER_FLAG=""
```

## Secret Variable Contract

Pipeline Variables UI 必須設定以下變數後 pipeline 才能成功執行：

| Variable Name | Secret | Required |
|--------------|--------|----------|
| `AZURE_DEVOPS_PAT` | Yes（打勾 Keep this value secret） | Yes |
| `AZURE_DEVOPS_ORG_URL` | No | Yes |

script step 的 `env:` block 注入方式：
```yaml
env:
  AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
  AZURE_DEVOPS_ORG_URL: $(AZURE_DEVOPS_ORG_URL)
```
