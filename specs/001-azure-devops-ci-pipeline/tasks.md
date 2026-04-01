# Tasks: Azure DevOps CI Pipeline

**Input**: Design documents from `/specs/001-azure-devops-ci-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks for Python code are included to ensure pipeline validity.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure: `pipelines/templates/`, `asgards/src/`, `asgards/tests/`
- [X] T002 Initialize `asgards/requirements.txt` with `pytest`, `pytest-cov`, and `ruff`
- [X] T003 [P] Configure linting rules in `asgards/.ruff.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `pipelines/templates/install-deps.yml` for Python environment setup
- [X] T005 [P] Create sample Python module in `asgards/src/main.py`
- [X] T006 [P] Create sample unit test in `asgards/tests/test_main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Python Validation (Priority: P1) 🎯 MVP

**Goal**: Automatically lint and test Python code on every commit.

**Independent Test**: Push a commit to a feature branch and verify that the Azure DevOps pipeline starts automatically and executes `pytest` and `ruff`.

### Implementation for User Story 1

- [X] T007 [US1] Create `pipelines/templates/run-tests.yml` to execute `pytest` and `ruff`
- [X] T008 [US1] Create `pipelines/main.yml` with Build and Test stages
- [X] T009 [US1] Configure CI triggers (batch: true) and branch filters in `pipelines/main.yml`
- [X] T010 [US1] Add publish test results and coverage tasks to `pipelines/templates/run-tests.yml`

**Checkpoint**: At this point, User Story 1 (MVP) is fully functional and testable independently.

---

## Phase 4: User Story 2 - SonarQube Quality Analysis (Priority: P2)

**Goal**: Integrate SonarQube analysis and enforce Quality Gates.

**Independent Test**: Verify that the SonarQube analysis task runs and that the pipeline fails if the Quality Gate result is 'Failed'.

### Implementation for User Story 2

- [X] T011 [US2] Create `pipelines/templates/sonarqube-analysis.yml` for preparation and analysis
- [X] T012 [US2] Update `pipelines/main.yml` to include the Analyze stage (depends on Test stage)
- [X] T013 [US2] Configure `SonarQubePublish` and `SonarQubeQualityGate` in `pipelines/templates/sonarqube-analysis.yml`
- [X] T014 [US2] Add SonarQube project properties to `pipelines/templates/sonarqube-analysis.yml`

**Checkpoint**: At this point, all user stories are independently functional and integrated.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T015 [P] Validate `quickstart.md` setup instructions manually
- [X] T016 [P] Final review of pipeline YAML against the `pipeline-config.md` contract
- [X] T017 Cleanup temporary files and ensure `.gitignore` covers `__pycache__` and `.pytest_cache`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 (for test coverage data)
- **Polish (Final Phase)**: Depends on all user stories being complete

### Parallel Opportunities

- T003, T005, and T006 can be worked on in parallel.
- All Phase N tasks marked [P] can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1).
3. **STOP and VALIDATE**: Verify automated validation works on a push.

### Incremental Delivery

1. Foundation ready.
2. Add US1 -> Test independently (MVP!).
3. Add US2 -> Test integration with US1.
