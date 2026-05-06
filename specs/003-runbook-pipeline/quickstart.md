# Quickstart: Runbook Pipeline

## 前置條件

1. Azure DevOps 組織已存在且有 `ubuntu-latest` hosted agent 可用
2. 本 repo 已在 Azure DevOps 上設定為 pipeline 的 source

## 步驟 1：設定 Secret Variables

在 Azure DevOps 的 Pipeline → Edit → Variables 新增：

| Name | Value | Secret |
|------|-------|--------|
| `AZURE_DEVOPS_PAT` | 你的 Personal Access Token | ✅ 打勾 |
| `AZURE_DEVOPS_ORG_URL` | `https://dev.azure.com/yourorg` | ❌ |

## 步驟 2：建立 Pipeline

1. Azure DevOps → Pipelines → New Pipeline
2. 選擇 repo → 選擇 "Existing Azure Pipelines YAML file"
3. 指定路徑：`/pipelines/runbook-pipeline.yml`
4. 儲存（不要直接執行）

## 步驟 3：執行 create_project

1. 點選 "Run Pipeline"
2. 填入 Parameters：
   - **選擇 Runbook**: `create_project`
   - **專案名稱**: `MyNewProject`
   - **Pipeline 名稱**: `CI Pipeline`（可保留預設）
   - **Project Manager emails**: `pm@company.com`（空白分隔多筆）
   - **Project Member emails**: `dev1@company.com dev2@company.com`
3. 點 Run，觀察 log 確認各步驟成功

## 步驟 4：執行 modify_member

1. 點選 "Run Pipeline"
2. 填入 Parameters：
   - **選擇 Runbook**: `modify_member`
   - **專案名稱**: `MyNewProject`
   - **新增 Project Member emails**: `newdev@company.com`
3. 點 Run

## 驗證

- Pipeline log 中應看到 `[OK]` 訊息
- Pipeline 最終狀態為綠色（Succeeded）
- 若 pre-check 失敗（如專案已存在），log 顯示 `[!!]` 並以紅色失敗結束

## 疑難排解

| 症狀 | 原因 | 解法 |
|------|------|------|
| `ValueError: PAT required` | Secret variable 未設定 | 檢查 Pipeline Variables 中 `AZURE_DEVOPS_PAT` |
| `ModuleNotFoundError: asgards` | install step 失敗 | 確認 `asgards/setup.py` 存在 |
| `專案 'xxx' 已存在` | pre-check 擋住 | 換一個新的專案名稱 |
