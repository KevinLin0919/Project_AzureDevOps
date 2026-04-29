"""
create_project runbook

流程：
  Pre-check  → 建立 Project → 建立 Repo → 推送 pipelines/
  → 建立 Build → 建立分支 [develop, uat, master, hotfix]
  → 套用 Branch Policies → 建立群組並加入成員

使用方式：
  python runbooks/create_project.py --project MyProject \\
      --managers pm@co.com --members dev1@co.com dev2@co.com

必要環境變數：AZURE_DEVOPS_PAT、AZURE_DEVOPS_ORG_URL
"""

import argparse
import os
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from asgards import (
    GROUP_PROJECT_MANAGER,
    GROUP_PROJECT_MEMBER,
    BranchClient,
    MemberClient,
    PipelineClient,
    ProjectClient,
    RepoClient,
)

_PIPELINES_DIR = Path(__file__).parent.parent / "pipelines"
_YAML_REPO_PATH = "pipelines/main.yml"
_MAIN_BRANCH = "main"
_BRANCHES = ["develop", "uat", "master", "hotfix"]

# ── 輔助 ──────────────────────────────────────────────────────────────────────


def _section(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _info(msg: str) -> None:
    print(f"  [--]  {msg}")


def _err(msg: str) -> None:
    print(f"  [!!]  {msg}")


# ── 各步驟 ────────────────────────────────────────────────────────────────────


def _pre_check(project_api: ProjectClient, project_name: str) -> bool:
    _section("Pre-check")
    _info(f"Repo 名稱將與專案名稱相同：'{project_name}'")
    _ok("Repo 名稱符合規則")

    if project_api.exists(project_name):
        _err(f"專案 '{project_name}' 已存在，中止執行")
        return False

    _ok(f"專案 '{project_name}' 尚未存在，可以建立")
    return True


def _create_project(project_api: ProjectClient, project_name: str) -> str:
    _section("1. 建立 Project")
    _info(f"建立專案 '{project_name}'...")
    project_api.create(project_name, description="", process_template="Agile")
    _ok("建立完成，等待 Azure 初始化 (10s)...")
    time.sleep(10)
    project = project_api.get(project_name)
    _ok(f"Project ID: {project.id}")
    return project.id


def _create_repo(repo_api: RepoClient, project_name: str) -> str:
    _section("2. 建立 Repo")
    _info(f"建立 Repo '{project_name}'...")
    repo = repo_api.create(project_name, project_name)
    _ok(f"Repo 建立完成，ID: {repo.id}")

    _info("初始化 main branch (README.md)...")
    repo_api.push_file(
        project_name,
        repo.id,
        "/README.md",
        content=f"# {project_name}\n",
        branch=_MAIN_BRANCH,
        commit_message="chore: initial commit",
    )
    _ok("main branch 初始化完成")
    _ok("5MB 大小限制：已由 RepoClient.push_file 強制執行（所有 repo 均適用）")
    return repo.id


def _push_pipeline(repo_api: RepoClient, project_name: str, repo_id: str) -> None:
    _section("3. 推送 pipelines/ 資料夾")
    # main.yml 引用了 templates/ 下的 4 個檔案，全部一起推才能正常執行
    pipeline_files = sorted(_PIPELINES_DIR.rglob("*.yml"))
    for src in pipeline_files:
        rel = src.relative_to(_PIPELINES_DIR.parent)
        _info(f"推送 {rel} ...")
        repo_api.push_file(
            project_name,
            repo_id,
            f"/{rel}",
            content=src.read_text(encoding="utf-8"),
            branch=_MAIN_BRANCH,
            commit_message=f"chore: add {rel}",
        )
        _ok(f"{rel} 推送完成")


def _create_pipeline(
    pipeline_api: PipelineClient, project_name: str, pipeline_name: str, repo_id: str
) -> int:
    _section("4. 建立 Build Pipeline")
    _info(f"建立 '{pipeline_name}' (指向 {_YAML_REPO_PATH})...")
    definition = pipeline_api.create_from_yaml(
        project_name,
        pipeline_name,
        repo_id,
        _YAML_REPO_PATH,
        default_branch=_MAIN_BRANCH,
    )
    _ok(f"Pipeline 建立完成，Definition ID: {definition.id}")
    return definition.id


def _create_branches(branch_api: BranchClient, project_name: str, repo_id: str) -> None:
    _section("5. 建立分支")
    for branch in _BRANCHES:
        _info(f"建立 '{branch}' (from {_MAIN_BRANCH})...")
        branch_api.create(project_name, repo_id, branch, source_ref=_MAIN_BRANCH)
        _ok(f"'{branch}' 建立完成")


def _set_branch_policies(branch_api: BranchClient, project_name: str, repo_id: str) -> None:
    _section("6. 套用 Branch Policies")
    for branch in _BRANCHES:
        _info(f"套用 policies 至 '{branch}'...")
        branch_api.set_all_policies(project_name, repo_id, branch)
        _ok(f"'{branch}': 綁定 Work Item ✓  解完 Comment ✓  Basic Merge only ✓")


def _setup_members(
    member_api: MemberClient,
    project_id: str,
    managers: list[str],
    members: list[str],
) -> None:
    _section("7. 設定成員群組")

    for group_name in [GROUP_PROJECT_MANAGER, GROUP_PROJECT_MEMBER]:
        _info(f"確認群組 '{group_name}' 存在（不存在則建立）...")
        member_api.get_or_create_group(project_id, group_name)
        _ok(f"群組 '{group_name}' 就緒")

    for email in managers:
        _info(f"加入 {GROUP_PROJECT_MANAGER}: {email}")
        member_api.add(project_id, GROUP_PROJECT_MANAGER, email)
        _ok("已加入")

    for email in members:
        _info(f"加入 {GROUP_PROJECT_MEMBER}: {email}")
        member_api.add(project_id, GROUP_PROJECT_MEMBER, email)
        _ok("已加入")

    if not managers and not members:
        _info("未指定成員，跳過加入步驟")


# ── 主流程 ────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="在 Azure DevOps 上建立標準化專案環境",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "範例：\n"
            "  python runbooks/create_project.py --project MyProject\n"
            "  python runbooks/create_project.py --project MyProject \\\n"
            "      --pipeline-name 'CI Pipeline' \\\n"
            "      --managers pm@co.com \\\n"
            "      --members dev1@co.com dev2@co.com"
        ),
    )
    parser.add_argument("--project", required=True, help="專案名稱（同時作為 Repo 名稱）")
    parser.add_argument(
        "--pipeline-name", default="CI Pipeline", help="Pipeline 顯示名稱（預設：CI Pipeline）"
    )
    parser.add_argument(
        "--managers", nargs="*", default=[], metavar="EMAIL", help="加入 ProjectManager 的 email 清單"
    )
    parser.add_argument(
        "--members", nargs="*", default=[], metavar="EMAIL", help="加入 ProjectMember 的 email 清單"
    )
    return parser.parse_args()


def run() -> None:
    args = _parse_args()
    pat = os.getenv("AZURE_DEVOPS_PAT", "")
    org_url = os.getenv("AZURE_DEVOPS_ORG_URL", "")

    print("\n" + "=" * 60)
    print("  create_project runbook")
    print(f"  專案：{args.project}")
    print(f"  組織：{org_url or '(未設定 AZURE_DEVOPS_ORG_URL)'}")
    print("=" * 60)

    if not pat or not org_url:
        _err("請先設定環境變數 AZURE_DEVOPS_PAT 與 AZURE_DEVOPS_ORG_URL")
        return

    project_api = ProjectClient(pat=pat, org_url=org_url)
    repo_api = RepoClient(pat=pat, org_url=org_url)
    pipeline_api = PipelineClient(pat=pat, org_url=org_url)
    branch_api = BranchClient(pat=pat, org_url=org_url)
    member_api = MemberClient(pat=pat, org_url=org_url)

    if not _pre_check(project_api, args.project):
        return

    try:
        project_id = _create_project(project_api, args.project)
        repo_id = _create_repo(repo_api, args.project)
        _push_pipeline(repo_api, args.project, repo_id)
        _create_pipeline(pipeline_api, args.project, args.pipeline_name, repo_id)
        _create_branches(branch_api, args.project, repo_id)
        _set_branch_policies(branch_api, args.project, repo_id)
        _setup_members(member_api, project_id, args.managers, args.members)

        print("\n" + "=" * 60)
        print(f"  完成！專案 '{args.project}' 已建置完畢。")
        print("=" * 60 + "\n")

    except Exception as e:
        _err(f"執行失敗: {e}")
        raise


if __name__ == "__main__":
    run()
