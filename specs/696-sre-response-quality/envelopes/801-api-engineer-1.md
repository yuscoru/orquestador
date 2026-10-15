# Task Envelope — 801 — api-engineer — slice 1 of 5 (E1)

Issued 2026-10-15 by the admiral. Immutable once sent.

Slice note: Task #801 is executed in five sequential envelopes (E1–E5), one `api-engineer` invocation at a
time, per `handoff.md` `recommended_execution_order`. E1 is the first envelope for this repository and
therefore also authorizes materialization of the local feature directory.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT

feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality

assignment:
  ado_task: 801
  spec_tasks:
    - T003
    - T004
    - T005
    - T006

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Materialize the local feature directory for this repository (first envelope), then deliver the RBAC
  slice of the quality read contract: the new capability quality.view exists in the static catalog, is
  included in the predefined user role seed for new deployments, and is granted once, idempotently, to the
  predefined user role of existing deployments by a flagged startup backfill that runs last in the startup
  block. Administrators must keep access through the existing admin bypass.

acceptance_criteria:
  - Local specs/696-sre-response-quality/ exists with spec.md, plan.md and tasks.md projected from the global artifacts, task ids preserved exactly (T003-T026 as work; T001 and T002 are withdrawn and must not appear as pending work), and the repository's local plan.md carries the soarplus-api section (7.1) of the global plan.
  - .specify/feature.json points to specs/696-sre-response-quality (see constraints on the untracked .specify/).
  - Tests for T003 are written first and fail before the implementation exists.
  - quality.view is registered in api/rbac_capabilities.py with a description, and is part of the predefined user baseline seed.
  - A one-shot, flagged, idempotent backfill adds quality.view to the predefined user role of existing deployments, never overrides a role from which an administrator later removed it, and is invoked last in the startup block of DatabaseService.__init__.
  - require_capability is not used for this capability; the gate to be used by later routes is authorize_capability_or_admin (no route is added in this envelope).
  - tests/test_rbac_capabilities.py and tests/test_predefined_roles_seeding.py still pass.
  - No route, controller, model or collection access for quality data is added in this envelope.
  - GET /db/collections and GET /db/collections/{collection_name} are not modified.
  - T003-T006 are marked complete in the local tasks.md only if their validation passed; IMPLEMENTATION-CHECKPOINT.md exists and records the current state, what was validated, and any baseline test failures that pre-date this work.

contracts:
  consumes: []
  provides:
    - name: quality.view
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-02-quality-view-capability

dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Document-shape data contract is stable and not needed by this slice.

constraints:
  - Follow the repository constitution, AGENTS.md, .github/copilot-instructions.md and applicable scoped instructions; tests first.
  - The working tree already contains uncommitted changes and untracked files that are NOT part of this assignment (modified .gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py; untracked .agents/, .env.local.example, .github/, .specify/, .vscode/, AGENTS.md, scripts/run_local.sh). Do not modify, revert, stage or commit them. Stage explicit paths only; never use "git add -A" or "git add .".
  - HEAD is one local commit ahead of its remote branch (580a532). Do not push (see delivery).
  - .specify/ is currently untracked in this repository. Write .specify/feature.json, but do not commit the untracked .specify/ directory wholesale. If the file cannot be committed on its own without committing unrelated untracked content, leave it uncommitted and report it as a warning.
  - Run the baseline of the RBAC suites before changing code and record any failure that pre-dates this work separately from failures you cause.
  - Do not run /speckit.specify, /speckit.plan or /speckit.tasks. Project the local artifacts from source.artifacts.
  - Do not touch any other repository. Do not mark any task outside T003-T006 as complete.
  - If the planned approach is unworkable or a task is not satisfiable as written, return a blocker for the captain; do not rewrite the plan locally.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in code, commits, ADO comments or the result.

validation_expectations:
  - Focused unit tests for T003 pass.
  - tests/test_rbac_capabilities.py and tests/test_predefined_roles_seeding.py pass, or pre-existing failures are separated and evidenced.
  - Backfill idempotency and "runs last" are covered by tests, not only by reading the code.
  - Report any acceptance criterion that could not be verified.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```
