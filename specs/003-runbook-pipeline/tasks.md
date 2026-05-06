# Tasks: Runbook Pipeline

**Input**: Design documents from `/specs/003-runbook-pipeline/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**唯一交付物**: `pipelines/runbook-pipeline.yml`（不修改任何現有檔案）

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可並行執行（不同檔案，無依賴）
- **[Story]**: 對應 spec.md 的 User Story（US1 = create_project、US2 = modify_member）
- 每個 task 含精確檔案路徑

---

## Phase 1: Setup

**Purpose**: 建立 pipeline YAML 檔案

- [x] T001 在 `pipelines/runbook-pipeline.yml` 建立空白檔案

---

## Phase 2: Foundational（YAML 骨架）

**Purpose**: 所有 runbook 共用的骨架，必須在 US1/US2 之前完成

**⚠️ CRITICAL**: User Story 實作需等此 phase 完成

- [x] T002 在 `pipelines/runbook-pipeline.yml` 加入 `trigger: none` 與 `pool: vmImage: ubuntu-latest`
- [x] T003 在 `pipelines/runbook-pipeline.yml` 加入完整 `parameters:` 區段，包含 9 個 parameters（runbook enum、project_name、pipeline_name、managers、members、add_manager、remove_manager、add_member、remove_member），依 `contracts/pipeline-params.md` 的 YAML block
- [x] T004 在 `pipelines/runbook-pipeline.yml` 加入 `steps:` 區段與 `UsePythonVersion@0` task（versionSpec: '3.11'）
- [x] T005 在 `pipelines/runbook-pipeline.yml` 加入 install step：`pip install -r asgards/requirements.txt && pip install -e asgards/`

**Checkpoint**: YAML 骨架完成，有效的 Azure DevOps pipeline 格式，可進行 US1/US2 實作

---

## Phase 3: User Story 1 - create_project via UI（Priority: P1）🎯 MVP

**Goal**: 使用者在 Pipeline UI 選擇 `create_project`，填入參數後 agent 自動執行 `runbooks/create_project.py`

**Independent Test**: 在 Azure DevOps UI 手動觸發，選 `create_project`，填入測試專案名稱，確認 pipeline 成功且 Azure DevOps 上出現對應專案

### Implementation for User Story 1

- [x] T006 [US1] 在 `pipelines/runbook-pipeline.yml` 加入 `${{ if eq(parameters.runbook, 'create_project') }}:` 條件式 script step，包含：
  - shell conditional 處理 `managers` 與 `members` 空字串（`[ -n "$MANAGERS" ] && MANAGERS_FLAG="--managers $MANAGERS" || MANAGERS_FLAG=""`）
  - 呼叫 `python runbooks/create_project.py --project "$PROJECT_NAME" --pipeline-name "$PIPELINE_NAME" $MANAGERS_FLAG $MEMBERS_FLAG`
  - `env:` block 注入 `AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)`、`AZURE_DEVOPS_ORG_URL: $(AZURE_DEVOPS_ORG_URL)`、`PROJECT_NAME`、`PIPELINE_NAME`、`MANAGERS`、`MEMBERS`（均來自對應 parameters）
  - `displayName: 'Run create_project runbook'`

**Checkpoint**: US1 完成，在 Pipeline UI 可選 `create_project` 並成功執行整個建立流程

---

## Phase 4: User Story 2 - modify_member via UI（Priority: P2）

**Goal**: 使用者在 Pipeline UI 選擇 `modify_member`，填入參數後 agent 自動執行 `runbooks/modify_member.py`

**Independent Test**: 手動觸發，選 `modify_member`，填入現有專案名稱和 email，確認成員群組正確變更

### Implementation for User Story 2

- [x] T007 [US2] 在 `pipelines/runbook-pipeline.yml` 加入 `${{ if eq(parameters.runbook, 'modify_member') }}:` 條件式 script step，包含：
  - shell conditional 處理 `add_manager`、`remove_manager`、`add_member`、`remove_member` 四個空字串（各自用 `[ -n "$VAR" ] && FLAG="--flag $VAR" || FLAG=""` 模式）
  - 呼叫 `python runbooks/modify_member.py --project "$PROJECT_NAME" $ADD_MANAGER_FLAG $REMOVE_MANAGER_FLAG $ADD_MEMBER_FLAG $REMOVE_MEMBER_FLAG`
  - `env:` block 注入 `AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)`、`AZURE_DEVOPS_ORG_URL: $(AZURE_DEVOPS_ORG_URL)`、`PROJECT_NAME`、`ADD_MANAGER`、`REMOVE_MANAGER`、`ADD_MEMBER`、`REMOVE_MEMBER`（均來自對應 parameters）
  - `displayName: 'Run modify_member runbook'`

**Checkpoint**: US1 + US2 均可獨立執行，pipeline 根據 `runbook` 參數正確分流

---

## Phase 5: Polish & 驗證

**Purpose**: 確認整體品質並對照 quickstart.md 驗證

- [x] T008 對照 `specs/003-runbook-pipeline/contracts/pipeline-params.md` 檢查 `pipelines/runbook-pipeline.yml` 中所有 parameter 名稱與型別是否一致
- [x] T009 確認 `pipelines/runbook-pipeline.yml` 不含任何 hardcoded token 或 org_url（違反 Constitution IX）
- [ ] T010 依照 `specs/003-runbook-pipeline/quickstart.md` 步驟 3 手動觸發 `create_project`，驗證 SC-001~SC-004

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1（Setup）**: 無依賴，立即開始
- **Phase 2（Foundational）**: 依賴 Phase 1，阻擋 US1/US2
- **Phase 3（US1）**: 依賴 Phase 2
- **Phase 4（US2）**: 依賴 Phase 2，可與 Phase 3 並行
- **Phase 5（Polish）**: 依賴 Phase 3 + Phase 4

### User Story Dependencies

- **US1（P1）**: Phase 2 完成後即可開始，無跨 story 依賴
- **US2（P2）**: Phase 2 完成後即可開始，可與 US1 並行

### Parallel Opportunities

- T006（US1）與 T007（US2）可並行，它們修改同一檔案的不同 step 區塊
- T008、T009 可並行（T010 需在兩者完成後執行）

---

## Parallel Example: Phase 3 + 4 同時進行

```
完成 T005 後，可同時開始：
Task A: T006 - create_project 條件式 step
Task B: T007 - modify_member 條件式 step
（兩個 step 在同一 YAML 檔案不同位置，不衝突）
```

---

## Implementation Strategy

### MVP First（US1 Only）

1. 完成 Phase 1–2（骨架）
2. 完成 Phase 3（US1: create_project）
3. **STOP and VALIDATE**：手動觸發 `create_project` 確認可用
4. 再完成 Phase 4（US2: modify_member）

### 完整交付順序

T001 → T002 → T003 → T004 → T005 → T006 + T007（並行）→ T008 + T009（並行）→ T010
