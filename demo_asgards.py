"""
Asgards Demo - 完整的 Azure DevOps 自動化流程展示

情境：公司新開一個專案，從零開始設定好整個 Azure DevOps 環境。
流程：建立專案 → 建立 Repo → 加入成員 → 建立 Pipeline → 設定保留政策 → 建立分支並套用 Policy

使用前請設定環境變數：
    export AZURE_DEVOPS_PAT="你的 Personal Access Token"
    export AZURE_DEVOPS_ORG_URL="https://dev.azure.com/你的組織名稱"
"""

import os

from asgards import (
    BranchClient,
    MemberClient,
    PipelineClient,
    ProjectClient,
    ReleaseClient,
    RepoClient,
)

# ── 設定 ──────────────────────────────────────────────────────────────────────

PAT = os.getenv("AZURE_DEVOPS_PAT", "")
ORG_URL = os.getenv("AZURE_DEVOPS_ORG_URL", "")

PROJECT_NAME = "MyNewProject"
REPO_NAME = "my-service"
PIPELINE_NAME = "CI Pipeline"
YAML_PATH = "pipelines/main.yml"
MAIN_BRANCH = "main"
DEV_BRANCH = "develop"

NEW_MEMBER_EMAIL = "newdev@company.com"


# ── 輔助函式 ──────────────────────────────────────────────────────────────────

def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def info(msg: str) -> None:
    print(f"  [--]  {msg}")


def err(msg: str) -> None:
    print(f"  [!!]  {msg}")


# ── Demo 各階段 ───────────────────────────────────────────────────────────────

def demo_project(project_api: ProjectClient) -> str | None:
    """建立專案，若已存在則直接取得 ID。"""
    section("1. Project")

    if project_api.exists(PROJECT_NAME):
        info(f"專案 '{PROJECT_NAME}' 已存在，跳過建立")
    else:
        info(f"建立專案 '{PROJECT_NAME}'...")
        project_api.create(PROJECT_NAME, description="Demo project", process_template="Agile")
        ok(f"專案 '{PROJECT_NAME}' 建立完成（非同步，Azure 需幾秒處理）")

    project = project_api.get(PROJECT_NAME)
    ok(f"專案 ID: {project.id}")
    return project.id


def demo_repo(repo_api: RepoClient, project_id: str) -> str | None:
    """建立 Repo 並示範檔案操作。"""
    section("2. Repository")

    # 建立 Repo
    info(f"建立 Repo '{REPO_NAME}'...")
    repo = repo_api.create(PROJECT_NAME, REPO_NAME)
    ok(f"Repo 建立完成，ID: {repo.id}")

    # 推送第一個檔案
    info("推送 README.md...")
    repo_api.push_file(
        PROJECT_NAME,
        repo.id,
        "/README.md",
        content=f"# {REPO_NAME}\n\n此 Repo 由 Asgards 自動建立。\n",
        branch=MAIN_BRANCH,
        commit_message="chore: initial commit",
    )
    ok("README.md 推送完成")

    # 示範：從另一個 Repo 複製檔案
    # info("從來源 Repo 複製 .gitignore...")
    # content = repo_api.get_file_content_from_source(
    #     src_org_url=ORG_URL,
    #     src_pat=PAT,
    #     src_project="TemplateProject",
    #     src_repo="templates",
    #     file_path="/.gitignore",
    # )
    # repo_api.push_file(PROJECT_NAME, repo.id, "/.gitignore", content)
    # ok(".gitignore 複製完成")

    # 示範：5MB 限制保護
    section("2b. 5MB 檔案限制保護")
    large_content = "X" * (6 * 1024 * 1024)
    info(f"嘗試推送 {len(large_content) / 1024 / 1024:.0f}MB 的檔案...")
    try:
        repo_api.push_file(PROJECT_NAME, repo.id, "/huge.bin", large_content)
    except ValueError as e:
        ok(f"成功攔截！{e}")

    return repo.id


def demo_member(member_api: MemberClient, project_id: str) -> None:
    """將新成員加入 Contributors 群組。"""
    section("3. Member Management")

    info(f"將 '{NEW_MEMBER_EMAIL}' 加入 Contributors...")
    member_api.add(project_id, "Contributors", NEW_MEMBER_EMAIL)
    ok("加入成功")

    info("列出 Contributors 成員：")
    members = member_api.list_members(project_id, "Contributors")
    for m in members:
        print(f"       - {m.mail_address or m.principal_name}")


def demo_pipeline(pipeline_api: PipelineClient, repo_id: str) -> int | None:
    """從 YAML 建立 Pipeline 並觸發一次執行。"""
    section("4. Pipeline")

    info(f"建立 Pipeline '{PIPELINE_NAME}' (指向 {YAML_PATH})...")
    definition = pipeline_api.create_from_yaml(
        PROJECT_NAME,
        PIPELINE_NAME,
        repo_id,
        YAML_PATH,
        default_branch=MAIN_BRANCH,
    )
    ok(f"Pipeline 建立完成，Definition ID: {definition.id}")

    info("觸發第一次 Build...")
    build = pipeline_api.trigger(PROJECT_NAME, definition.id)
    ok(f"Build 已排入佇列，Build ID: {build.id}")

    status = pipeline_api.get_run_status(PROJECT_NAME, build.id)
    info(f"目前狀態: {status}")

    return definition.id


def demo_release(release_api: ReleaseClient) -> None:
    """設定 Release 保留政策。"""
    section("5. Release Retention Policy")

    info("套用保留政策...")
    release_api.set_retention_settings(
        PROJECT_NAME,
        days_to_keep_deleted_runs=7,     # UI 刪除後保留 7 天
        days_to_keep=30,                  # 預設保留 30 天
        maximum_days_to_keep=90,          # 最多保留 90 天
        maximum_runs_to_keep=10,          # 最多保留 10 個 build
        retain_associated_build=True,     # 保留關聯的 Build 記錄
    )
    ok("保留政策設定完成")

    current = release_api.get_retention_settings(PROJECT_NAME)
    info("目前設定：")
    for key, value in current.items():
        print(f"       {key}: {value}")


def demo_branch(branch_api: BranchClient, repo_id: str) -> None:
    """建立 develop 分支並套用三項 Policy。"""
    section("6. Branch & Policies")

    info(f"從 '{MAIN_BRANCH}' 建立 '{DEV_BRANCH}' 分支...")
    branch_api.create(PROJECT_NAME, repo_id, DEV_BRANCH, source_ref=MAIN_BRANCH)
    ok(f"分支 '{DEV_BRANCH}' 建立完成")

    info(f"套用 Branch Policies 至 '{DEV_BRANCH}'...")
    branch_api.set_all_policies(PROJECT_NAME, repo_id, DEV_BRANCH)
    ok("Policy 套用完成：")
    print("       - Work Item 綁定（PR 必須關聯 Work Item）")
    print("       - Comment Resolution（PR 留言必須全部解完）")
    print("       - Merge 策略：Basic Merge（No Fast-Forward）")


# ── 主流程 ────────────────────────────────────────────────────────────────────

def run_demo() -> None:
    print("\n" + "=" * 60)
    print("  Asgards Demo - Azure DevOps 自動化環境建置")
    print("=" * 60)
    print(f"  組織：{ORG_URL or '(未設定 AZURE_DEVOPS_ORG_URL)'}")

    if not PAT or not ORG_URL:
        print("\n[!!] 請先設定環境變數再執行 Demo：")
        print("     export AZURE_DEVOPS_PAT='your-pat'")
        print("     export AZURE_DEVOPS_ORG_URL='https://dev.azure.com/your-org'")
        return

    project_api = ProjectClient(pat=PAT, org_url=ORG_URL)
    repo_api = RepoClient(pat=PAT, org_url=ORG_URL)
    member_api = MemberClient(pat=PAT, org_url=ORG_URL)
    pipeline_api = PipelineClient(pat=PAT, org_url=ORG_URL)
    release_api = ReleaseClient(pat=PAT, org_url=ORG_URL)
    branch_api = BranchClient(pat=PAT, org_url=ORG_URL)

    try:
        project_id = demo_project(project_api)
        repo_id = demo_repo(repo_api, project_id)
        demo_member(member_api, project_id)
        demo_pipeline(pipeline_api, repo_id)
        demo_release(release_api)
        demo_branch(branch_api, repo_id)

        print("\n" + "=" * 60)
        print("  全部完成！Azure DevOps 環境已自動建置完畢。")
        print("=" * 60 + "\n")

    except Exception as e:
        err(f"發生錯誤: {e}")
        raise


if __name__ == "__main__":
    run_demo()
