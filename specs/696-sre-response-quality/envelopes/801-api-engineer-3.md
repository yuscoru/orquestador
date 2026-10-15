# Task Envelope — 801 — api-engineer — slice 3 of 5 (E3)

Issued 2026-10-15 by the admiral. Immutable once sent.

Slice note: third of five sequential envelopes for Task #801. E1 (commit d2b4df9) and E2 (commit bad615b) are
completed; the local feature directory, the capability, the models, the data-access layer and the controller
module already exist.

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
    - T012
    - T013
    - T014
    - T015
    - T016

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Expose the first two routes of the quality read contract, behind the quality.view gate - R1, the catalog
  of evaluated targets, and R2, the paginated history of one target - as designed in plan.md section 3 and
  section 7.1. Together with E1 and E2 this is the deliverable MVP of the evolution view.

acceptance_criteria:
  - Tests for T012 (R1) and T015 (R2) are written first and fail before the implementation exists.
  - R1 GET /quality/targets returns one item per (target_type, target) with eval_profile and latest taken from the most recent valid point, evaluations counting valid points only, filters target_type and eval_profile (enums), ordering by target_type then target ascending, limit default 100 bounded 1-500, offset >= 0, and an items/total envelope; values outside bounds yield 422.
  - R1 does not add a derived "kind" or "is_orchestrator" field; orchestrators are selected through the persisted eval_profile only.
  - R2 GET /quality/targets/{target_type}/{target}/evaluations returns EvaluationPoint items ordered by timestamp then eval_run_id (deterministic with equal timestamps), for order desc (default) and asc, limit default 50 bounded 1-200, offset >= 0, an items/total envelope; a target with zero valid points returns 404 with a Spanish detail message.
  - Each EvaluationPoint carries evaluated_at, window (from, to, n, min_sample), status (one of the five contract statuses), sample_sufficient, evaluator (profile, profile version, judge model) and metrics with both metric ids always present; an unscored metric is value null, never 0; two points that differ in profile version or judge model are distinguishable from the point data alone.
  - Both routes declare response_model, are served by a new api/routes/quality.py with prefix /quality and tag Quality, and are registered in api/api.py (import, include_router, and a tag entry in the tags_metadata).
  - Both routes are gated by authorize_capability_or_admin(controller, "quality.view"), defined once at module level and used as a dependency; require_capability is not used; there are no routes without the gate. Tests assert the dependency by introspection, in the style of the existing capability-gate tests.
  - User input is validated and used only as an equality literal; operator-injection strings are rejected (422) or treated as literals; this is covered by tests.
  - Blocking pymongo calls are not executed on the event loop (asyncio.to_thread or equivalent already provided by the controller).
  - T013 states which catalog strategy was used and why - preferred is a server-side aggregation (valid points -> latest per key plus count); if the live engine cannot be exercised, say so, and if the controller-side reduction over a sorted list of valid points is kept, justify it with an explicit bound on the data volume and the projection weight and record the risk. Whichever is used is recorded in IMPLEMENTATION-CHECKPOINT.md.
  - GET /db/collections and GET /db/collections/{collection_name} are not modified. The API creates no index on agent_eval_results and never writes to it. No response of R1 or R2 contains any FR-009 field.
  - The new tests pass, the RBAC suites pass, and the full unit suite shows no failure beyond the 5 recorded baseline failures (test_usage x2, test_llm_providers_manage_own_capability x3); any other failure is yours to fix.
  - T012-T016 are marked complete in the local tasks.md only if their validation passed; IMPLEMENTATION-CHECKPOINT.md is updated with current reality (including the catalog strategy and what remains unverified against a live DocumentDB).

contracts:
  consumes:
    - name: agent_eval_results document v4
      provider: soarplus-agentics
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-03-agent-eval-result-document
    - name: quality.view
      provider: soarplus-api
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-02-quality-view-capability
  provides:
    - name: quality-read-api
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api

dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Document shape is stable; no change needed there.

constraints:
  - Follow the repository constitution, AGENTS.md, .github/copilot-instructions.md and the scoped python-fastapi and testing instructions; tests first.
  - The pre-existing uncommitted modifications and untracked files (.gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py, .agents/, .env.local.example, .github/, .specify/ except feature.json, .vscode/, AGENTS.md, scripts/run_local.sh) are not part of this assignment; do not modify, revert, stage or commit them; stage explicit paths only; never git add -A or git add .
  - Work in small verifiable steps and commit as soon as the assigned tasks validate, so that an interruption cannot leave only uncommitted work. Always finish by returning a Task Result or a Blocker Result as your final message; if running short of room, stop at a validated state, commit it and return a PARTIAL result listing the remaining work precisely.
  - Do not push. Do not touch any other repository. Do not mark any task outside T012-T016 as complete.
  - Do not add R3, R4 or R5 (detail, cases, metric descriptors); they belong to E4.
  - Do not use the MTA controller or the /agents/tasks code as a template for async behaviour or paging bounds; use Query(ge, le).
  - If the planned approach is unworkable or a task is not satisfiable as written, return a blocker for the captain; do not rewrite the plan locally.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in code, commits, ADO comments or the result. When commenting on Azure DevOps, use the Azure DevOps integration for project SOARPLUS and Task #801 only, and confirm the comment by reading it back.

validation_expectations:
  - Focused unit tests for T012 and T015 pass; route gate and bounds covered by tests.
  - Allow-list guarantee for R1 and R2 responses covered by tests.
  - RBAC suites pass; full suite compared against the recorded baseline.
  - Report any acceptance criterion that could not be verified, including anything that needs a live DocumentDB.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```
