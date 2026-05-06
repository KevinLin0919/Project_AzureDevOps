# Research: Runbook Pipeline

**Branch**: `003-runbook-pipeline` | **Phase**: 0

## Decision 1: 空 email 清單的 shell 傳遞方式

**Problem**: 兩支 runbook 的 email 參數均使用 `nargs="*"` + `default=[]`。Pipeline parameter 預設為空字串 `""`，若直接展開 `--managers ${{ parameters.managers }}`，空字串會讓 argparse 收到 `[""]` 而非 `[]`。

**Decision**: 在 script step 使用 shell 條件變數，只在值非空時加上對應 flag：

```bash
[ -n "$MANAGERS" ] && MANAGERS_FLAG="--managers $MANAGERS" || MANAGERS_FLAG=""
python runbooks/create_project.py ... $MANAGERS_FLAG
```

**Rationale**: 明確且可讀；word-splitting 讓空白分隔的多筆 email 自然展開為多個 argparse 值；不需修改現有 runbook 程式碼。

**Alternatives considered**:
- 直接 `--managers ${{ parameters.managers }}`：空字串時 argparse 收到 `[""]`，造成 API 呼叫失敗。
- `${{ if ne(parameters.managers, '') }}` 條件式 step：語法冗長，每個 email 參數都需要一個獨立 step。

---

## Decision 2: Secret Variable 注入方式

**Decision**: 在每個 script step 的 `env:` block 中注入：

```yaml
env:
  AZURE_DEVOPS_PAT: $(AZURE_DEVOPS_PAT)
  AZURE_DEVOPS_ORG_URL: $(AZURE_DEVOPS_ORG_URL)
```

**Rationale**: `$(VAR)` 是 Azure DevOps macro syntax，在 runtime 展開 pipeline variable（含 secret）；注入為環境變數後，`_auth.py` 的 `os.environ.get()` 直接讀取，完全不需修改現有程式碼。Secret variable 的值在 log 中會自動遮蔽。

**Alternatives considered**:
- 寫死在 YAML：明顯違反 Constitution IX，禁止。
- Variable Group：功能等同，但需額外在 Library 建立 group，對單一 pipeline 而言過度複雜。

---

## Decision 3: asgards 安裝方式

**Decision**: install step 執行：

```bash
pip install -r asgards/requirements.txt
pip install -e asgards/
```

**Rationale**: `setup.py` 已正確宣告 `packages=find_packages()`，`pip install -e .` 建立 editable install，讓 `import asgards` 直接可用。移除 runbook 裡的 `sys.path.insert` hack 依賴（pipeline 上無效）。

**Alternatives considered**:
- `PYTHONPATH=. python runbooks/...`：需要每個 script step 都設定，容易遺漏。
- `pip install asgards/`（非 editable）：functional 等同，但 editable install 在未來本地開發也有用。

---

## Decision 4: 條件式執行語法

**Decision**: 使用 Azure DevOps compile-time template expression：

```yaml
- ${{ if eq(parameters.runbook, 'create_project') }}:
  - script: ...
```

**Rationale**: Template expression 在 pipeline 解析時展開，只有被選中的 step 會出現在執行計畫中，清楚且高效。

**Alternatives considered**:
- Bash `if` 條件在單一 script step：所有 runbook 邏輯混在一個 step，難以閱讀與維護。
- 多個 condition: 用 `condition: eq(...)` 在 step 層級：step 仍出現在執行計畫中只是被跳過，較不直觀。
