# Feature Specification: Runbook Pipeline

**Feature Branch**: `003-runbook-pipeline`
**Created**: 2026-05-07
**Status**: Draft
**Input**: User description: "新增一條 Azure DevOps pipeline，檔案放在 pipelines/runbook-pipeline.yml。這條 pipeline 透過 runtime parameters 讓使用者在 UI 選擇要執行哪個 runbook，並填入對應參數，由 pipeline agent 執行對應的 Python script。觸發方式：trigger: none，只允許手動執行。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 透過 UI 執行 create_project runbook (Priority: P1)

工程師在 Azure DevOps 的 Pipeline UI 點選「Run Pipeline」，選擇 runbook 為 `create_project`，填入專案名稱、Pipeline 名稱，以及 Project Manager 和 Member 的 email，按下執行後 agent 自動完成整個建立專案的流程。

**Why this priority**: 這是整條 pipeline 的核心用途，讓原本只能在本地端手動執行的 runbook 可以由任何有權限的人在雲端觸發。

**Independent Test**: 在 Azure DevOps UI 手動觸發 pipeline，選擇 `create_project`，填入測試用的專案名稱，確認 agent 成功執行並建立出對應的 Azure DevOps 專案。

**Acceptance Scenarios**:

1. **Given** 使用者有 pipeline 執行權限，**When** 選擇 `create_project` 並填入有效的 `project_name`，**Then** pipeline 執行成功，Azure DevOps 中建立出對應專案、repo、branches 與 pipeline definition。
2. **Given** 使用者選擇 `create_project` 但填入的 `project_name` 已存在，**When** pipeline 執行，**Then** pipeline 記錄 pre-check 失敗訊息並以非零 exit code 結束，不重複建立專案。
3. **Given** `managers` 與 `members` 欄位留空，**When** 執行 `create_project`，**Then** pipeline 仍正常完成，僅跳過加入成員步驟。

---

### User Story 2 - 透過 UI 執行 modify_member runbook (Priority: P2)

工程師在 Pipeline UI 選擇 runbook 為 `modify_member`，填入目標專案名稱和要新增/移除的成員 email，執行後自動更新成員群組。

**Why this priority**: 第二個已實作的 runbook，功能完整但使用頻率低於建立專案。

**Independent Test**: 觸發 pipeline 並選擇 `modify_member`，填入現有專案名稱和一個有效 email，確認成員群組正確變更。

**Acceptance Scenarios**:

1. **Given** 目標專案存在，**When** 選擇 `modify_member` 並填入 `add_member`，**Then** 指定使用者被加入 ProjectMember 群組。
2. **Given** 目標專案不存在，**When** 選擇 `modify_member`，**Then** pipeline 記錄 pre-check 失敗並以非零 exit code 結束。
3. **Given** 所有新增/移除欄位皆為空，**When** 執行 `modify_member`，**Then** pipeline 執行完成並記錄「無任何變更」。

---

### Edge Cases

- 當 `AZURE_DEVOPS_PAT` 或 `AZURE_DEVOPS_ORG_URL` secret variable 未設定時，pipeline 應以清楚的錯誤訊息失敗，而非靜默失敗。
- 當 `managers` / `members` 等 email 欄位包含無效 email 格式時，runbook 執行失敗並記錄錯誤。
- 當同時填入 `add_member` 和 `remove_member` 相同的 email，兩個操作均依序執行（行為由 runbook 原有邏輯決定）。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: pipeline YAML 檔案 MUST 放置於 `pipelines/runbook-pipeline.yml`。
- **FR-002**: pipeline MUST 設定 `trigger: none`，禁止自動觸發，僅允許手動執行。
- **FR-003**: pipeline MUST 定義以下 runtime parameters，並在執行前於 UI 顯示：
  - `runbook`（string，必填，values: `create_project` / `modify_member`）
  - `project_name`（string，必填）
  - `pipeline_name`（string，預設 `"CI Pipeline"`）
  - `managers`（string，預設空字串，空白分隔的 email 清單）
  - `members`（string，預設空字串，空白分隔的 email 清單）
  - `add_manager` / `remove_manager` / `add_member` / `remove_member`（string，預設空字串）
- **FR-004**: pipeline 的 install step MUST 使用 `pip install -e asgards/` 正確安裝 asgards package，不得依賴 `sys.path.insert` hack。
- **FR-005**: pipeline MUST 根據 `runbook` 參數值，以條件式執行對應的 Python script（`runbooks/create_project.py` 或 `runbooks/modify_member.py`）。
- **FR-006**: `AZURE_DEVOPS_PAT` 與 `AZURE_DEVOPS_ORG_URL` MUST 透過 Pipeline secret variables 提供，並在 script step 以 `env:` 注入為環境變數，不得寫死在 YAML 中。
- **FR-007**: runbook Python script 的 exit code MUST 被 pipeline 正確捕捉，失敗時 pipeline 整體標記為失敗。

### Key Entities

- **Pipeline YAML**：`pipelines/runbook-pipeline.yml`，定義 parameters、steps 與條件式執行邏輯。
- **Secret Variables**：在 Azure DevOps Pipeline UI 設定的 `AZURE_DEVOPS_PAT` 與 `AZURE_DEVOPS_ORG_URL`，不進版控。
- **Runbook Scripts**：`runbooks/create_project.py` 與 `runbooks/modify_member.py`，本體不需修改。
- **asgards package**：`asgards/`，由 install step 安裝後供 runbook import 使用。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% 的手動觸發均能在 UI 中選擇 runbook 並填入參數後成功執行。
- **SC-002**: `create_project` runbook 的端對端執行時間（從觸發到完成）在 3 分鐘以內。
- **SC-003**: 當 credentials 未設定或 pre-check 失敗時，pipeline 100% 以非零 exit code 結束，並留下可讀的錯誤訊息。
- **SC-004**: pipeline 不引入任何新的 Python 程式碼，runbook 與 asgards 原始檔案保持不變。

## Assumptions

- **A-001**: Azure DevOps 組織已有可用的 agent pool（使用 `ubuntu-latest` hosted agent）。
- **A-002**: `AZURE_DEVOPS_PAT` 與 `AZURE_DEVOPS_ORG_URL` 由執行者在 Pipeline Variables UI 手動設定，不透過 Variable Group。
- **A-003**: runbook Python script 本身已經過本地端驗證，本 feature 不包含修改 runbook 邏輯。
- **A-004**: Python 3.11 為 pipeline agent 的執行環境。
- **A-005**: `managers`、`members` 等 email 參數在 UI 中以空白字元分隔多筆，由 shell 展開後傳入 script 的 `--managers` / `--members` 參數。
