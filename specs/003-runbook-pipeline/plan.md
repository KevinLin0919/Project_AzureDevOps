# Implementation Plan: Runbook Pipeline

**Branch**: `003-runbook-pipeline` | **Date**: 2026-05-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-runbook-pipeline/spec.md`

## Summary

新增 `pipelines/runbook-pipeline.yml`，讓使用者透過 Azure DevOps Pipeline UI 的 runtime parameters 選擇執行 `create_project` 或 `modify_member` runbook，credentials 由 Pipeline secret variables 透過 `env:` 注入，不修改任何現有程式碼。

## Technical Context

**Language/Version**: Python 3.11（pipeline agent 執行環境）
**Primary Dependencies**: azure-devops SDK（asgards 依賴）、asgards package（local editable install）
**Storage**: N/A（pipeline 為無狀態執行）
**Testing**: 手動觸發驗證（YAML 本身無 pytest 測試）
**Target Platform**: Azure DevOps hosted agent（ubuntu-latest）
**Project Type**: Azure DevOps pipeline YAML（單一新增檔案）
**Performance Goals**: create_project 端對端 < 3 分鐘（SC-002）
**Constraints**: 不修改現有任何檔案；credentials 不得寫死；空 email 參數需正確處理
**Scale/Scope**: 1 個 YAML 檔，2 個 runbook，9 個 parameters

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Scalable Pipelines | ✅ PASS | YAML 放在 `pipelines/`，結構符合規範 |
| II. Automated CI/CD | ✅ PASS | `trigger: none` 是刻意的，runbook 為操作型動作而非程式碼變更，例外合理 |
| III. SonarQube Quality | N/A | 此 pipeline 不含 Python build，無需 SonarQube |
| IV. Standardized Structure | ✅ PASS | 僅新增 `pipelines/runbook-pipeline.yml` |
| V–VII. Python Reliability | N/A | 不新增 Python 程式碼 |
| VIII. API Layer Design | N/A | 不修改 asgards |
| IX. Authentication Contract | ✅ PASS | PAT 透過 secret variable + env: 注入，未寫死 |

## Project Structure

### Documentation (this feature)

```text
specs/003-runbook-pipeline/
├── plan.md              ← 本檔案
├── research.md          ← Phase 0：4 項設計決策
├── data-model.md        ← Phase 1：parameter schema + 執行流程
├── quickstart.md        ← Phase 1：操作手冊
├── contracts/
│   └── pipeline-params.md  ← Phase 1：YAML + CLI mapping contract
└── tasks.md             ← Phase 2（/speckit.tasks 產出）
```

### Source Code（新增）

```text
pipelines/
├── main.yml                  ← 已存在，不修改
├── runbook-pipeline.yml      ← 新增（本 feature 唯一交付物）
└── templates/                ← 已存在，不修改
```

## Key Design Decisions（from research.md）

1. **空 email 清單**：shell conditional `[ -n "$VAR" ] && FLAG="--opt $VAR" || FLAG=""` 處理 nargs="*" 的空字串問題
2. **Secret 注入**：`env:` block 搭配 `$(AZURE_DEVOPS_PAT)` macro syntax
3. **asgards 安裝**：`pip install -r asgards/requirements.txt && pip install -e asgards/`
4. **條件式執行**：`${{ if eq(parameters.runbook, 'xxx') }}` compile-time template expression

## Complexity Tracking

無 Constitution 違規，不需要此表格。
