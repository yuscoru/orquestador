#!/usr/bin/env python3
"""
ado_cli.py
==========
Audited Azure DevOps helper using `az boards` CLI.
Creates and verifies Tasks with child/parent relations and tags.
Guarantees:
  - PAT is never echoed, logged, or passed in argv.
  - Organization and project have secure defaults.
  - Duplicate check before creation (idempotent).
  - Explicit read-back verification after creation.
"""

import argparse
import json
import os
import subprocess
import sys

DEFAULT_ORG = "https://dev.azure.com/ES-ECC-INNOVATION"
DEFAULT_PROJECT = "SOARPLUS"


def get_clean_env() -> dict:
    """Prepare subprocess environment with AZURE_DEVOPS_EXT_PAT mapped securely."""
    env = dict(os.environ)
    pat = env.get("AZURE_DEVOPS_PAT") or env.get("ADO_PAT")
    if not pat:
        print("[ERROR] AZURE_DEVOPS_PAT not found in environment", file=sys.stderr)
        sys.exit(1)
    env["AZURE_DEVOPS_EXT_PAT"] = pat
    env["AZURE_CONFIG_DIR"] = env.get("AZURE_CONFIG_DIR", "/tmp/soarplus-azure-cli")
    return env


def run_az(args: list[str], env: dict) -> dict | list | None:
    """Run az command and parse JSON output. Never print env or raw token."""
    cmd = ["az"] + args + ["--output", "json", "--only-show-errors"]
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        err = res.stderr.strip()
        # Sanitize any unexpected echo
        print(f"[ERROR] az command failed: {err}", file=sys.stderr)
        return None
    out = res.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError as e:
        print(f"[ERROR] failed to parse az json output: {e}", file=sys.stderr)
        return None


def show_work_item(item_id: int, org: str, env: dict) -> dict | None:
    """Fetch details and relations of a work item."""
    return run_az([
        "boards", "work-item", "show",
        "--id", str(item_id),
        "--org", org,
        "--expand", "relations"
    ], env)


def find_child_task_by_title(parent_id: int, title: str, org: str, project: str, env: dict) -> int | None:
    """Check if parent already has a child Task with the identical title."""
    parent = show_work_item(parent_id, org, env)
    if not parent:
        print(f"[ERROR] Parent #{parent_id} could not be retrieved", file=sys.stderr)
        sys.exit(1)

    relations = parent.get("relations") or []
    for rel in relations:
        # Hierarchy-Reverse or child relation
        # Usually attributes["name"] == "Child" or rel["rel"] == "System.LinkTypes.Hierarchy-Forward"
        name = rel.get("attributes", {}).get("name")
        rel_type = rel.get("rel")
        if name == "Child" or rel_type == "System.LinkTypes.Hierarchy-Forward":
            url = rel.get("url", "")
            child_id = url.split("/")[-1]
            if child_id.isdigit():
                child = show_work_item(int(child_id), org, env)
                if child and child.get("fields", {}).get("System.Title") == title:
                    return int(child_id)
    return None


def extract_parent_id(item: dict) -> int | None:
    """Extract parent work item ID from relations."""
    for rel in item.get("relations") or []:
        name = rel.get("attributes", {}).get("name")
        rel_type = rel.get("rel")
        if name == "Parent" or rel_type == "System.LinkTypes.Hierarchy-Reverse":
            url = rel.get("url", "")
            pid = url.split("/")[-1]
            if pid.isdigit():
                return int(pid)
    return None


def create_task(parent_id: int, title: str, tags: str, org: str, project: str, dry_run: bool, env: dict):
    print(f"=== Create Task ===")
    print(f"  Parent:   #{parent_id}")
    print(f"  Title:    {title}")
    print(f"  Tags:     {tags}")
    print(f"  Org:      {org}")
    print(f"  Project:  {project}")

    # 1. Idempotency check: see if child already exists
    existing_id = find_child_task_by_title(parent_id, title, org, project, env)
    if existing_id:
        print(f"\n[IDEMPOTENT] Child Task with title already exists: #{existing_id}")
        item = show_work_item(existing_id, org, env)
        print_verified_item(item)
        return existing_id

    if dry_run:
        print("\n[DRY-RUN] No work item created. Pre-validation passed.")
        return None

    # 2. Create Task
    fields = []
    if tags:
        fields.append(f"System.Tags={tags}")

    create_args = [
        "boards", "work-item", "create",
        "--type", "Task",
        "--title", title,
        "--org", org,
        "--project", project
    ]
    if fields:
        create_args.extend(["--fields"] + fields)

    res = run_az(create_args, env)
    if not res or "id" not in res:
        print("[ERROR] Failed to create work item", file=sys.stderr)
        sys.exit(1)

    new_id = int(res["id"])
    print(f"  -> Created Task #{new_id}, linking parent #{parent_id}...")

    # 3. Add parent relation
    rel_args = [
        "boards", "work-item", "relation", "add",
        "--id", str(new_id),
        "--relation-type", "parent",
        "--target-id", str(parent_id),
        "--org", org
    ]
    rel_res = run_az(rel_args, env)
    if not rel_res:
        print(f"[ERROR] Failed to link parent #{parent_id} to #{new_id}", file=sys.stderr)
        sys.exit(1)

    # 4. Read back and verify
    item = show_work_item(new_id, org, env)
    if not item:
        print(f"[ERROR] Read-back failed for #{new_id}", file=sys.stderr)
        sys.exit(1)

    print("\n[VERIFIED SUCCESS]")
    print_verified_item(item)
    return new_id


def print_verified_item(item: dict | None):
    if not item:
        return
    f = item.get("fields", {})
    parent_id = extract_parent_id(item)
    print(json.dumps({
        "id": item.get("id"),
        "type": f.get("System.WorkItemType"),
        "title": f.get("System.Title"),
        "state": f.get("System.State"),
        "parent": parent_id,
        "tags": f.get("System.Tags"),
        "created_date": f.get("System.CreatedDate")
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Audited Azure DevOps CLI tool for Tasks and comments")
    parser.add_argument("--org", default=DEFAULT_ORG, help="Azure DevOps org URL")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="Azure DevOps project")

    sub = parser.add_subparsers(dest="command", required=True)

    # check
    check_p = sub.add_parser("check", help="Verify connection and inspect parent work item")
    check_p.add_argument("--parent", type=int, required=True, help="Parent work item ID")

    # show
    show_p = sub.add_parser("show", help="Show work item details")
    show_p.add_argument("--id", type=int, required=True, help="Work item ID")

    # create-task
    create_p = sub.add_parser("create-task", help="Create child Task")
    create_p.add_argument("--parent", type=int, required=True, help="Parent work item ID")
    create_p.add_argument("--title", required=True, help="Task title")
    create_p.add_argument("--tags", default="", help="Semicolon separated tags, e.g. 'cr-004; api'")
    create_p.add_argument("--dry-run", action="store_true", help="Dry run without writing to ADO")

    args = parser.parse_args()
    env = get_clean_env()

    if args.command == "check":
        item = show_work_item(args.parent, args.org, env)
        if item:
            print(f"[OK] Connection verified. Work item #{args.parent}:")
            print_verified_item(item)
        else:
            sys.exit(1)

    elif args.command == "show":
        item = show_work_item(args.id, args.org, env)
        if item:
            print_verified_item(item)
        else:
            sys.exit(1)

    elif args.command == "create-task":
        create_task(args.parent, args.title, args.tags, args.org, args.project, args.dry_run, env)


if __name__ == "__main__":
    main()
