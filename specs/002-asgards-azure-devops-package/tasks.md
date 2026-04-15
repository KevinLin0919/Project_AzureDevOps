---
description: "Task list for 002-asgards-azure-devops-package"
---

# Tasks: Asgards — Azure DevOps Python Package

**Input**: Design documents from `/specs/002-asgards-azure-devops-package/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅

**Test approach**: All tests use `unittest.mock` to mock SDK clients.
No real Azure DevOps credentials required to run the test suite.

**CI gate**: After each module phase, the full pipeline must pass:
`ruff check asgards/` → `pytest asgards/tests/` → SonarCloud quality gate.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1=Project, US2=Repo, US3=Member, US4=Pipeline, US5=Release, US6=Branch

---

## Phase 1: Setup (Package Scaffold)

**Purpose**: Make the `asgards` package pip-installable before any module work begins.

- [ ] T001 Create `asgards/setup.py` with `name="asgards"`, `version="0.1.0"`, `packages=find_packages()`, and `install_requires=["azure-devops>=7.1.0b4", "msrest>=0.7.1", "requests>=2.31"]`
- [ ] T002 Update `asgards/__init__.py` with placeholder `__all__ = []` and a version comment (final imports added in T024)
- [ ] T003 Verify package is installable locally: `pip install -e asgards/` — confirm no import errors

**Checkpoint**: `from asgards import *` runs without error. ✓

---

## Phase 2: Foundational (Shared Auth Helper)

**Purpose**: The `_build_connection()` helper is used by all 6 modules. Must exist before any module implementation.

⚠️ **CRITICAL**: No module work can begin until T004–T005 are complete.

- [ ] T004 Create `asgards/src/_auth.py` implementing `_build_connection(pat, org_url) -> Connection` — reads `AZURE_DEVOPS_PAT` / `AZURE_DEVOPS_ORG_URL` as fallback, raises `ValueError` if either is missing
- [ ] T005 [P] Write `asgards/tests/test_auth.py` — test: missing PAT raises `ValueError`; missing org_url raises `ValueError`; constructor arg overrides env var; valid inputs return a `Connection` instance (mock `Connection.__init__`)

**Checkpoint**: Foundation ready — all 6 module phases can now proceed sequentially. ✓

---

## Phase 3: US1 — Project Management (Priority: P1) 🎯 MVP

**Goal**: CRUD operations and existence check for Azure DevOps projects.

**Independent Test**: `from asgards import ProjectClient; c = ProjectClient(pat="x", org_url="https://dev.azure.com/org")` succeeds; all 5 methods callable with mocked `CoreClient`.

- [ ] T006 [US1] Implement `asgards/src/project.py` — `ProjectClient` with methods: `create(name, description, process_template)`, `get(project_id_or_name)`, `list()`, `delete(project_id)`, `exists(name)` — follow contract in `contracts/project-client.md`; `exists()` must catch 404 and return `False`
- [ ] T007 [US1] Write `asgards/tests/test_project.py` — mock `azure.devops.connection.Connection`; test: `create()` calls `queue_create_project`; `get()` calls `get_project`; `list()` calls `get_projects`; `delete()` calls `queue_delete_project`; `exists()` returns `True` when found and `False` on 404
- [ ] T008 [US1] Run `ruff check asgards/src/project.py asgards/tests/test_project.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_project.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 4: US2 — Repository Operations (Priority: P2)

**Goal**: Repo CRUD, cross-source file retrieval, file push as commit, 5 MB guard.

**Independent Test**: All 7 `RepoClient` methods callable with mocked `GitClient`; `push_file()` raises `ValueError` for content over 5 MB without making any API call.

- [ ] T009 [US2] Implement `asgards/src/repo.py` — `RepoClient` with: `create`, `get`, `list`, `delete`, `get_file_content`, `get_file_content_from_source` (builds a separate `Connection` with `src_pat`/`src_org_url`), `push_file` (validates 5 MB before API call; detects add vs edit via `get_item()`) — follow contract in `contracts/repo-client.md`
- [ ] T010 [US2] Write `asgards/tests/test_repo.py` — mock `Connection` and `GitClient`; test: `create/get/list/delete` call correct SDK methods; `get_file_content_from_source` builds a second connection with source credentials; `push_file` raises `ValueError` when `len(content) > 5*1024*1024`; `push_file` uses `change_type=1` for new file and `change_type=2` for existing file
- [ ] T011 [US2] Run `ruff check asgards/src/repo.py asgards/tests/test_repo.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_repo.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 5: US3 — Member Management (Priority: P3)

**Goal**: Find `Project Administrators` / `Contributors` groups by name; add and remove members.

**Independent Test**: All 4 `MemberClient` methods callable with mocked `GraphClient`; `find_group()` raises `RuntimeError` when group name not found.

- [ ] T012 [US3] Implement `asgards/src/member.py` — `MemberClient` with: `find_group(project_id, group_display_name)`, `add(project_id, group_display_name, user_email)`, `remove(project_id, group_display_name, user_email)`, `list_members(project_id, group_display_name)`; expose module-level constants `GROUP_PROJECT_ADMINISTRATORS` and `GROUP_CONTRIBUTORS` — follow contract in `contracts/member-client.md`
- [ ] T013 [US3] Write `asgards/tests/test_member.py` — mock `GraphClient`; test: `find_group()` filters by `display_name` and raises `RuntimeError` when not found; `add()` calls `add_member_to_group` with correct descriptors; `remove()` calls `remove_member_from_group`; `list_members()` calls `list_memberships`
- [ ] T014 [US3] Run `ruff check asgards/src/member.py asgards/tests/test_member.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_member.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 6: US4 — Pipeline Configuration (Priority: P4)

**Goal**: Create a build pipeline from a YAML file path; trigger runs; query status.

**Independent Test**: All 4 `PipelineClient` methods callable with mocked `BuildClient`; `get_run_status()` returns normalized string (`"queued"`, `"running"`, `"succeeded"`, `"failed"`, `"canceled"`), never a raw SDK enum.

- [ ] T015 [US4] Implement `asgards/src/pipeline.py` — `PipelineClient` with: `create_from_yaml(project, name, repo_id, yaml_path, default_branch)` using `process={"yamlFilename": yaml_path, "type": 2}`, `list(project)`, `trigger(project, definition_id)`, `get_run_status(project, build_id)` with status normalization — follow contract in `contracts/pipeline-client.md`
- [ ] T016 [US4] Write `asgards/tests/test_pipeline.py` — mock `BuildClient`; test: `create_from_yaml` calls `create_definition` with YAML process type `2`; `trigger` calls `queue_build`; `get_run_status` returns `"queued"` for `notStarted`, `"running"` for `inProgress`, `"succeeded"` for succeeded result, `"failed"` for failed result
- [ ] T017 [US4] Run `ruff check asgards/src/pipeline.py asgards/tests/test_pipeline.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_pipeline.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 7: US5 — Release Retention Policy (Priority: P5)

**Goal**: Read and partially update the 5 retention settings under Project Settings → Pipelines → Retention.

**Independent Test**: `get_retention_settings()` returns a dict with all 5 keys; `set_retention_settings()` with only one kwarg updates only that field and leaves others unchanged (read-modify-write pattern).

- [ ] T018 [US5] Implement `asgards/src/release.py` — `ReleaseClient` with: `get_retention_settings(project)` returning `{"days_to_keep_deleted_runs", "days_to_keep", "maximum_days_to_keep", "maximum_runs_to_keep", "retain_associated_build"}`; `set_retention_settings(project, **kwargs)` doing read-modify-write via `build_client.get_build_settings()` + `update_build_settings()` — follow contract in `contracts/release-client.md`
- [ ] T019 [US5] Write `asgards/tests/test_release.py` — mock `BuildClient`; test: `get_retention_settings` maps SDK fields to the 5 spec keys; `set_retention_settings` with one kwarg calls `get_build_settings` first then `update_build_settings`; passing no kwargs is a no-op (update not called or called with unchanged values)
- [ ] T020 [US5] Run `ruff check asgards/src/release.py asgards/tests/test_release.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_release.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 8: US6 — Branch Management (Priority: P6)

**Goal**: Create a branch from a source ref; enforce three branch policies (work item, comment resolution, merge strategy).

**Independent Test**: `create()` calls `update_refs` with correct `old_object_id` of 40 zeros for new branch; `set_policy_merge_strategy()` creates policy config with `allowNoFastForward=True` and all other merge modes `False`.

- [ ] T021 [US6] Implement `asgards/src/branch.py` — `BranchClient` with: `create(project, repo_id, branch_name, source_ref)` resolving branch name to SHA via `get_refs()` if needed; `set_policy_work_item`, `set_policy_comment_resolution`, `set_policy_merge_strategy` each calling `policy_client.create_policy_configuration`; `set_all_policies` calling all three; define `POLICY_*` constants — follow contract in `contracts/branch-client.md`
- [ ] T022 [US6] Write `asgards/tests/test_branch.py` — mock `GitClient` and `PolicyClient`; test: `create()` calls `update_refs` with 40-zero old_object_id; source branch name is resolved to SHA before create; `set_policy_merge_strategy()` passes `allowNoFastForward=True`, `allowSquash=False`, `allowRebase=False`, `allowRebaseMerge=False`; `set_all_policies()` calls all three policy setters
- [ ] T023 [US6] Run `ruff check asgards/src/branch.py asgards/tests/test_branch.py` and fix all reported issues

**Checkpoint**: `pytest asgards/tests/test_branch.py` passes. `ruff check asgards/` clean. ✓

---

## Phase 9: Polish & Integration

**Purpose**: Wire everything together, validate full coverage, confirm CI passes end-to-end.

- [ ] T024 Update `asgards/__init__.py` — add imports for all 6 clients: `ProjectClient`, `RepoClient`, `MemberClient`, `PipelineClient`, `ReleaseClient`, `BranchClient`; set `__all__` to the list of all 6 names
- [ ] T025 [P] Run full test suite: `pytest asgards/tests/ --cov=asgards/src --cov-report=term-missing` — confirm all tests pass and coverage report shows no untested branches in core logic
- [ ] T026 [P] Run `ruff check asgards/` — confirm zero issues across all modules
- [ ] T027 Review `specs/002-asgards-azure-devops-package/quickstart.md` — verify all code samples reflect the final implementation (update any method signatures that changed during implementation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all module phases**
- **US1–US6 (Phases 3–8)**: All depend on Phase 2; must run **sequentially** (one module per CI cycle)
- **Polish (Phase 9)**: Depends on all module phases complete

### Module Execution Order (strictly sequential per user prompt)

```
Phase 1 → Phase 2 → Phase 3 (US1) → CI ✓ → Phase 4 (US2) → CI ✓
→ Phase 5 (US3) → CI ✓ → Phase 6 (US4) → CI ✓
→ Phase 7 (US5) → CI ✓ → Phase 8 (US6) → CI ✓ → Phase 9
```

### Parallel Opportunities Within Each Module Phase

Within each module phase, T0X6 (implement) must complete before T0X7 (test) can be verified,
but T0X8 (ruff) can run against the source file as soon as T0X6 is done:

```bash
# Example for US1 (Project):
# Step 1: implement
Task: "Implement asgards/src/project.py"
# Step 2: parallel
Task: "Write asgards/tests/test_project.py"  [parallel with ruff check]
Task: "Run ruff check asgards/src/project.py"
```

---

## Implementation Strategy

### MVP (Phase 1 + 2 + 3 only)

1. Complete Phase 1: setup.py + __init__.py scaffold
2. Complete Phase 2: `_auth.py` shared helper
3. Complete Phase 3: `project.py` + tests
4. **STOP AND VALIDATE**: `pytest asgards/tests/` passes; `ruff check asgards/` clean; `pip install -e asgards/` works
5. Push to CI — verify pipeline green

### Incremental Delivery (Phases 3–8 one at a time)

Each module phase adds one independently-testable capability:
- After Phase 3: Package manages Projects ✓
- After Phase 4: + manages Repositories ✓
- After Phase 5: + manages Members ✓
- After Phase 6: + manages Pipelines ✓
- After Phase 7: + manages Retention policies ✓
- After Phase 8: + manages Branches and Policies ✓

---

## Notes

- `[P]` tasks = different files, no blocking dependencies on incomplete tasks
- Each module phase is self-contained: one source file + one test file + one ruff check
- `asgards/src/main.py` and `asgards/tests/test_main.py` (weeks 1–3) are **untouched**
- All 27 tasks are sized for a single `/speckit.implement` invocation (one task at a time)
