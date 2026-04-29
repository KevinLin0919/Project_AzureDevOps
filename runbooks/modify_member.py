"""
modify_member runbook

將對應人員加入或移除 ProjectManager / ProjectMember 群組。

使用方式：
  python runbooks/modify_member.py --project MyProject \\
      --add-manager pm@co.com \\
      --add-member dev@co.com \\
      --remove-member ex@co.com

必要環境變數：AZURE_DEVOPS_PAT、AZURE_DEVOPS_ORG_URL
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from asgards import GROUP_PROJECT_MANAGER, GROUP_PROJECT_MEMBER, MemberClient, ProjectClient

# ── 輔助 ──────────────────────────────────────────────────────────────────────


def _section(title: str) -> None:
    print(f"\n{'=' * 60}\n  {title}\n{'=' * 60}")


def _ok(msg: str) -> None:
    print(f"  [OK]  {msg}")


def _info(msg: str) -> None:
    print(f"  [--]  {msg}")


def _err(msg: str) -> None:
    print(f"  [!!]  {msg}")


# ── 步驟 ──────────────────────────────────────────────────────────────────────


def _pre_check(project_api: ProjectClient, project_name: str, changes: list[dict]) -> bool:
    _section("Pre-check")

    if not project_api.exists(project_name):
        _err(f"專案 '{project_name}' 不存在，中止執行")
        return False

    _ok(f"專案 '{project_name}' 存在")
    _ok(f"共 {len(changes)} 筆變更待執行")
    return True


def _apply_changes(member_api: MemberClient, project_id: str, changes: list[dict]) -> None:
    _section("套用成員變更")

    if not changes:
        _info("無任何變更")
        return

    for change in changes:
        action: str = change["action"]
        group: str = change["group"]
        email: str = change["email"]

        if action == "add":
            _info(f"加入 [{group}]: {email}")
            member_api.add(project_id, group, email)
            _ok("已加入")
        else:
            _info(f"移除 [{group}]: {email}")
            member_api.remove(project_id, group, email)
            _ok("已移除")


# ── 主流程 ────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="將人員加入或移除 ProjectManager / ProjectMember 群組",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "範例：\n"
            "  python runbooks/modify_member.py --project MyProject \\\n"
            "      --add-manager pm@co.com \\\n"
            "      --add-member dev1@co.com dev2@co.com \\\n"
            "      --remove-member ex@co.com"
        ),
    )
    parser.add_argument("--project", required=True, help="目標專案名稱")
    parser.add_argument(
        "--add-manager", nargs="*", default=[], metavar="EMAIL", help="加入 ProjectManager"
    )
    parser.add_argument(
        "--remove-manager", nargs="*", default=[], metavar="EMAIL", help="移除 ProjectManager"
    )
    parser.add_argument(
        "--add-member", nargs="*", default=[], metavar="EMAIL", help="加入 ProjectMember"
    )
    parser.add_argument(
        "--remove-member", nargs="*", default=[], metavar="EMAIL", help="移除 ProjectMember"
    )
    return parser.parse_args()


def run() -> None:
    args = _parse_args()
    pat = os.getenv("AZURE_DEVOPS_PAT", "")
    org_url = os.getenv("AZURE_DEVOPS_ORG_URL", "")

    changes = (
        [{"action": "add",    "group": GROUP_PROJECT_MANAGER, "email": e} for e in args.add_manager]
        + [{"action": "remove", "group": GROUP_PROJECT_MANAGER, "email": e} for e in args.remove_manager]
        + [{"action": "add",    "group": GROUP_PROJECT_MEMBER,  "email": e} for e in args.add_member]
        + [{"action": "remove", "group": GROUP_PROJECT_MEMBER,  "email": e} for e in args.remove_member]
    )

    print("\n" + "=" * 60)
    print("  modify_member runbook")
    print(f"  專案：{args.project}")
    print(f"  組織：{org_url or '(未設定 AZURE_DEVOPS_ORG_URL)'}")
    print("=" * 60)

    if not pat or not org_url:
        _err("請先設定環境變數 AZURE_DEVOPS_PAT 與 AZURE_DEVOPS_ORG_URL")
        return

    project_api = ProjectClient(pat=pat, org_url=org_url)
    member_api = MemberClient(pat=pat, org_url=org_url)

    if not _pre_check(project_api, args.project, changes):
        return

    try:
        project = project_api.get(args.project)
        _apply_changes(member_api, project.id, changes)

        print("\n" + "=" * 60)
        print("  完成！成員變更已套用。")
        print("=" * 60 + "\n")

    except Exception as e:
        _err(f"執行失敗: {e}")
        raise


if __name__ == "__main__":
    run()
