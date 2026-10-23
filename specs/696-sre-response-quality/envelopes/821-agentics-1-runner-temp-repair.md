# Operational Envelope — agentics — temporary SystemDev runner repair (A1)

Issued 2026-10-21 by the admiral after explicit user authorization. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: OPERATIONS
feature:
  ado_user_story: 696
  slug: sre-response-quality

assignment:
  id: 696-agentics-6
  ado_task: 821
  spec_tasks: []

repository:
  name: soarplus-agentics
  path: /root/soarplus-agentics
  branch: feature/696-sre-response-quality
  expected_head: 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f

worker: agentics

objective: >
  Repair the temporary `/tmp/sre-system-dev-venv` runner installation by exposing unreachable
  validated commit `096ac69f2a9d20621f608c610d5f7b192cc15285` through a temporary Git source under
  `/tmp`, install runner 0.1.2 with verifiable VCS metadata, and prove the non-serving preflight.

preconditions:
  - Verify Agentics repository/branch/HEAD and inventory existing dirty state without touching it.
  - Verify runner source `/root/soarplus-runner` contains object `096ac69...`; do not create/delete/change any ref, worktree file, index, config or commit in that repository.
  - Inventory `/tmp/sre-system-dev-venv` and intended temporary source paths. Do not delete or replace any existing path; if safe in-place repair is impossible, return BLOCKED.

acceptance_criteria:
  - All created/modified artifacts are confined to `/tmp/sre-system-dev-venv` and a clearly named `/tmp` runner source/bundle path. No versioned repository or `/root` file changes.
  - Temporary Git source advertises a ref resolving exactly to `096ac69f2a9d20621f608c610d5f7b192cc15285` without modifying source-repository refs.
  - Runner installs into the existing/new temporary venv without duplicating the shared callagent dependency stack unnecessarily; preserve/use the documented `.pth` mechanism.
  - `importlib.metadata` reports runner version 0.1.2 and `direct_url.json.vcs_info.commit_id` exact `096ac69...`; ADK, Motor, Pydantic and runner imports pass.
  - Run only `dev_pod.py --user-judge-key` without `--serve`; preflight returns `ready:true`, SystemDevAgent/dev-jcorujo-agent identity and verified runner reference.
  - Do not start/listen on 8080, invoke an agent, connect/start API/frontend, execute evaluation, or write DocumentDB.
  - Return exact reproducible commands and measured `/tmp` size so the admiral can replace the invalid runbook subsection.

constraints:
  - No deletion, ref deletion, reset, cleanup, commit, push, ADO, PR, deploy or persistent Git configuration.
  - Do not print secrets; this operation must not require DB or judge secret values.

delivery:
  update_ado: false
  commit: false
  push: false
  create_pr: false
  deploy: false
```
